import urllib.request
import json

def get_geoloc():
    try:
        print("[geoloc] Module started")
        ip = urllib.request.urlopen("https://api.ipify.org").read().decode().strip()
        url = f"http://ip-api.com/json/{ip}"
        with urllib.request.urlopen(url) as response:
            data = json.load(response)

        if data.get('status') == 'success':
            output = (
                f"IP: {data.get('query')}\n"
                f"Country: {data.get('country')} ({data.get('countryCode')})\n"
                f"Region: {data.get('regionName')}\n"
                f"City: {data.get('city')}\n"
                f"ZIP: {data.get('zip')}\n"
                f"Latitude: {data.get('lat')}\n"
                f"Longitude: {data.get('lon')}\n"
                f"Timezone: {data.get('timezone')}\n"
                f"ISP: {data.get('isp')}\n"
                f"Org: {data.get('org')}\n"
            )
        else:
            output = f"Failed to geolocate IP {ip}: {data.get('message', 'Unknown error')}"
    except Exception as e:
        output = f"[geoloc] Error: {e}"
    print(output)

get_geoloc()
