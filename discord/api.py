from globals import *

def login(token):
    response = requests.get(f"{BASE_URL}/users/@me", headers={"Authorization": token})
    if response.status_code == 200:
        context.token = token
        context.user = json.loads(response.text, object_hook=lambda d: SimpleNamespace(**d)) # cache the user entirely
        return True
    
    print("invalid token")
    # TODO: add some message box or smn "you entered invalid token"
    return False