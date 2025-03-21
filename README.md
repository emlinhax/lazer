Lazer - Discord DM Removal Tool

Lazer is an open-source Python tool designed to quickly and efficiently delete direct messages (DMs) on Discord. With a simple PyQt6 interface, it streamlines bulk message removal.

Features

✅ Bulk delete DMs on Discord
✅ Simple, user-friendly GUI
✅ Uses Discord API for efficient message deletion

Installation

Requirements

Ensure Python is installed, then install dependencies:

pip install -r requirements.txt

Dependencies

Lazer requires:

pip install PyQt6 requests

Usage

Run the tool:

python lazer.py

Enter your Discord Token and Channel ID.

Start the deletion process and let Lazer handle the rest.

Getting Your Discord Token

Method: Network Requests

Open Discord in your browser.

Open Developer Tools (Ctrl + Shift + I or Cmd + Option + I).

Go to the Network tab and search messages.

Send a message in any DM.

Click a messages request, open the Headers tab.

Find the authorization header—this is your token.

⚠ Never share your token—it grants full account access!

Getting a DM Channel ID

Method: Developer Mode

Open Discord > User Settings.

Go to Advanced and enable Developer Mode.

Right-click the DM in the sidebar.

Select Copy Channel ID.

License

📝 Open-source under the MIT License.

Contributions

💡 Feel free to submit pull requests or report issues!
