def register(server):
    def echo(args, _server):
        print("[*] Echo module called with args:", args)
    server.register_command("echo", echo, "Echo the provided arguments back to the console.")
