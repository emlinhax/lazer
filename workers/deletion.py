from globals import *

class DeletionWorker(QThread):
    update_progress = pyqtSignal(int, int, str)
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str, str)

    def __init__(self, channels):
        super().__init__()
        self.channels = channels
        self.running = True
        self.headers = {"Authorization": context.token}
        self.user_id = None

    def run(self):
        try:
            self.user_id = self.get_user_id()
            total = len(self.channels)
            
            for idx, channel in enumerate(self.channels):
                if not self.running:
                    break
                
                try:
                    if channel["type"] == "dm":
                        self.process_dm(channel)
                    elif channel["type"] == "server":
                        self.process_server(channel)
                    
                    self.update_progress.emit(idx + 1, total, channel["name"])
                except Exception as e:
                    self.error_occurred.emit(str(e), channel["name"])
            
            self.finished.emit()
            
        except Exception as e:
            self.error_occurred.emit(str(e), "Global")

    def get_user_id(self):
        try:
            return requests.get(f"{BASE_URL}/users/@me", headers=self.headers).json()["id"]
        except:
            raise ValueError("Failed to get user ID")

    def process_dm(self, channel):
        self.delete_messages(channel["id"], channel["name"])

    def process_server(self, server):
        try:
            channels = requests.get(
                f"{BASE_URL}/guilds/{server['id']}/channels",
                headers=self.headers
            ).json()
            
            for ch in channels:
                if ch["type"] in [0, 5]:
                    self.delete_messages(ch["id"], f"{server['name']}/#{ch['name']}")
        except Exception as e:
            raise Exception(f"Server error: {str(e)}")

    def delete_messages(self, channel_id, context):
        before = None
        while self.running:
            params = {"limit": 100}
            if before:
                params["before"] = before
                
            try:
                messages = requests.get(
                    f"{BASE_URL}/channels/{channel_id}/messages",
                    headers=self.headers,
                    params=params
                ).json()
                
                for msg in messages:
                    if msg["author"]["id"] == self.user_id:
                        self.delete_message(msg["id"], channel_id)
                        time.sleep(0.95)
                
                if len(messages) < 100:
                    break
                before = messages[-1]["id"]
            except Exception as e:
                raise Exception(f"Message deletion failed: {str(e)}")

    def delete_message(self, message_id, channel_id):
        try:
            response = requests.delete(
                f"{BASE_URL}/channels/{channel_id}/messages/{message_id}",
                headers=self.headers
            )
            if response.status_code == 429:
                retry_after = response.json().get('retry_after', 1)
                time.sleep(retry_after)
                self.delete_message(message_id, channel_id)
            response.raise_for_status()
        except Exception as e:
            raise Exception(f"Delete failed: {str(e)}")

    def stop(self):
        self.running = False