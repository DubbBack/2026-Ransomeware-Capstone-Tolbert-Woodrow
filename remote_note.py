#!/usr/bin/env python3
"""
Run on Kali: type a note, and it is saved to the Windows VM's Desktop and
opened in Notepad on the VM's screen.

Connects over SSH (OpenSSH Server on Windows). The note is uploaded with SFTP,
then Notepad is started through a short-lived scheduled task so it appears in
the logged-in user's desktop session instead of the hidden SSH session.

Usage:
    python3 remote_note.py <windows-ip> -u <windows-user> [-n name.txt] [-P 22]
"""

import argparse
import base64
import getpass
import re
import sys
from datetime import datetime

try:
    import paramiko
except ImportError:
    sys.exit("paramiko is required:  sudo apt install python3-paramiko")


def get_user_text():
    print("Type your note. Enter a blank line to finish:")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "":
            break
        lines.append(line)
    return "\n".join(lines)


def run_powershell(client, script):
    """Run a PowerShell script on the Windows host and return its output."""
    encoded = base64.b64encode(script.encode("utf-16-le")).decode()
    _, stdout, stderr = client.exec_command(
        f"powershell -NoProfile -NonInteractive -EncodedCommand {encoded}"
    )
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    if exit_code != 0:
        raise RuntimeError(err or out or f"PowerShell exited with code {exit_code}")
    return out


OPEN_IN_NOTEPAD = r"""
$ErrorActionPreference = 'Stop'
$task = 'OpenNote_' + [guid]::NewGuid().ToString('N')
$user = "$env:USERDOMAIN\$env:USERNAME"
$action = New-ScheduledTaskAction -Execute 'notepad.exe' -Argument '"__PATH__"'
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $task -Action $action -Principal $principal -Settings $settings | Out-Null
Start-ScheduledTask -TaskName $task
Start-Sleep -Seconds 2
Unregister-ScheduledTask -TaskName $task -Confirm:$false
"""


def main():
    parser = argparse.ArgumentParser(description="Send a note to Notepad on a Windows VM.")
    parser.add_argument("host", help="Windows VM IP or hostname")
    parser.add_argument("-u", "--user", required=True, help="Windows username (the one logged in on the VM)")
    parser.add_argument("-P", "--port", type=int, default=22, help="SSH port (default 22)")
    parser.add_argument("-n", "--name", help="file name (default: note_<date>_<time>.txt)")
    args = parser.parse_args()

    text = get_user_text()
    if not text.strip():
        print("No text entered. Nothing sent.")
        return

    name = args.name or datetime.now().strftime("note_%Y-%m-%d_%H-%M-%S.txt")
    name = re.sub(r'[<>:"/\\|?*]', "_", name)  # strip characters Windows won't allow
    if not name.lower().endswith(".txt"):
        name += ".txt"

    password = getpass.getpass(f"Password for {args.user}@{args.host}: ")

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # fine for a lab VM
    try:
        client.connect(args.host, port=args.port, username=args.user,
                       password=password or None, timeout=10)

        desktop = run_powershell(client, "[Environment]::GetFolderPath('Desktop')")
        win_path = f"{desktop}\\{name}"

        # Upload the note (CRLF line endings + UTF-8 BOM so every Notepad version reads it right)
        sftp_path = "/" + win_path.replace("\\", "/")
        with client.open_sftp() as sftp, sftp.open(sftp_path, "wb") as f:
            f.write(text.replace("\n", "\r\n").encode("utf-8-sig") + b"\r\n")
        print(f"Saved to {win_path}")

        run_powershell(client, OPEN_IN_NOTEPAD.replace("__PATH__", win_path.replace("'", "''")))
        print("Opened in Notepad on the Windows VM.")
    except paramiko.AuthenticationException:
        sys.exit("Login failed: check the username and password.")
    except Exception as e:
        sys.exit(f"Error: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
