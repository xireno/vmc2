def register(server):
    """
    Register the geoloc command on the server.
    When run, it sends 'runmod geoloc' to the selected client and displays the result.
    """
    def geoloc_cmd(args, server):
        session = server.select_client()
        if not session:
            print("[!] No client selected.")
            return
        session.send("runmod geoloc")
        print("[*] Geolocation command sent, waiting for client output...")
        output = session.receive()
        if output:
            print("[Client Geolocation Info]\n" + output)
        else:
            print("[!] No response from client.")

    server.register_command("geoloc",geoloc_cmd,"Geolocate a client and return location info")
