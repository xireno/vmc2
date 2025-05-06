def run():
    import os
    import shutil
    import sqlite3
    import sys
    import platform
    from glob import glob
    from textwrap import shorten

    def print_table(rows, headers):
        col_widths = [max(len(str(item)) for item in col) for col in zip(*([headers] + rows))]
        fmt = " | ".join("{{:<{}}}".format(w) for w in col_widths)
        line = "-+-".join("-" * w for w in col_widths)
        print(fmt.format(*headers))
        print(line)
        for row in rows:
            print(fmt.format(*row))
        print()

    def chrome_history():
        history_paths = []
        sys_plat = platform.system()
        if sys_plat == "Windows":
            base = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data')
            history_paths = glob(os.path.join(base, '*', 'History'))
        elif sys_plat == "Darwin":
            base = os.path.expanduser('~/Library/Application Support/Google/Chrome')
            history_paths = glob(os.path.join(base, '*', 'History'))
        elif sys_plat == "Linux":
            base = os.path.expanduser('~/.config/google-chrome')
            history_paths = glob(os.path.join(base, '*', 'History'))
        else:
            print("Unsupported OS for Chrome.")
            return

        if not history_paths:
            print("Chrome history not found.")
            return

        for path in history_paths:
            profile = os.path.basename(os.path.dirname(path))
            tmp = f"chrome_history_{profile}.db"
            try:
                shutil.copy2(path, tmp)
                conn = sqlite3.connect(tmp)
                cursor = conn.cursor()
                print(f"\n=== Chrome History: Profile [{profile}] ===")
                headers = ["Time", "Title", "URL"]
                rows = []
                for row in cursor.execute(
                    "SELECT datetime(last_visit_time/1000000-11644473600,'unixepoch'), title, url "
                    "FROM urls ORDER BY last_visit_time DESC LIMIT 10"
                ):
                    # Truncate title and URL for readability
                    time = row[0] or ""
                    title = shorten(row[1] or "", width=30, placeholder="...") if row[1] else ""
                    url = shorten(row[2] or "", width=50, placeholder="...") if row[2] else ""
                    rows.append([time, title, url])
                print_table(rows, headers)
                conn.close()
                os.remove(tmp)
            except Exception as e:
                print(f"[ERROR] Failed to read Chrome profile {profile}: {e}")

    def firefox_history():
        sys_plat = platform.system()
        profile_glob = ""
        if sys_plat == "Windows":
            base = os.path.expandvars(r'%APPDATA%\Mozilla\Firefox\Profiles')
            profile_glob = os.path.join(base, '*')
        elif sys_plat == "Darwin":
            base = os.path.expanduser('~/Library/Application Support/Firefox/Profiles')
            profile_glob = os.path.join(base, '*')
        elif sys_plat == "Linux":
            base = os.path.expanduser('~/.mozilla/firefox')
            profile_glob = os.path.join(base, '*')
        else:
            print("Unsupported OS for Firefox.")
            return

        profiles = glob(profile_glob)
        found = False
        for profile in profiles:
            db_path = os.path.join(profile, 'places.sqlite')
            if os.path.exists(db_path):
                tmp = f"firefox_history_{os.path.basename(profile)}.db"
                try:
                    shutil.copy2(db_path, tmp)
                    conn = sqlite3.connect(tmp)
                    cursor = conn.cursor()
                    print(f"\n=== Firefox History: Profile [{os.path.basename(profile)}] ===")
                    headers = ["Time", "URL"]
                    rows = []
                    for row in cursor.execute(
                        "SELECT datetime(visit_date/1000000,'unixepoch'), url "
                        "FROM moz_places, moz_historyvisits WHERE moz_places.id=moz_historyvisits.place_id "
                        "ORDER BY visit_date DESC LIMIT 10"
                    ):
                        time = row[0] or ""
                        url = shorten(row[1] or "", width=70, placeholder="...") if row[1] else ""
                        rows.append([time, url])
                    print_table(rows, headers)
                    conn.close()
                    os.remove(tmp)
                    found = True
                except Exception as e:
                    print(f"[ERROR] Failed to read Firefox profile {profile}: {e}")
        if not found:
            print("Firefox history not found.")

    print("=== Browser History Dumper ===")
    chrome_history()
    firefox_history()
