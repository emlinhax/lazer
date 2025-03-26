from globals import *

class DataFetcher(QThread):
    data_loaded = pyqtSignal(list, list)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        try:
            dms = self.fetch_dms()
            servers = self.fetch_servers()
            self.data_loaded.emit(dms, servers)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def fetch_dms(self):
        try:
            dms = []
            channels = requests.get(f"{BASE_URL}/users/@me/channels", headers={"Authorization": context.token}).json()
            for ch in channels:
                if ch["type"] in [1, 3]:
                    recipients = [u["username"] for u in ch.get("recipients", [])]
                    # get timestamp for sorting
                    last_message_id = ch.get('last_message_id')
                    if last_message_id:
                        timestamp = (int(last_message_id) >> 22) + 1420070400000
                    else:
                        channel_id = int(ch['id'])
                        timestamp = (channel_id >> 22) + 1420070400000
                    dms.append({
                        "id": ch["id"],
                        "name": "DM with " + ", ".join(recipients),
                        "type": "dm",
                        "timestamp": timestamp
                    })
            # forgot this lowkey
            dms.sort(key=lambda x: x['timestamp'], reverse=True)
            return dms
        except Exception as e:
            print(f"Error fetching DMs: {e}")
            return []

    def fetch_servers(self):
        try:
            servers = []
            guilds = requests.get(f"{BASE_URL}/users/@me/guilds", headers={"Authorization": context.token}).json()
            for guild in guilds:
                servers.append({
                    "id": guild["id"],
                    "name": guild["name"],
                    "type": "server"
                })
            return servers
        except Exception as e:
            print(f"Error fetching servers: {e}")
            return []