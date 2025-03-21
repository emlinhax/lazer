Lazer - Discord DM Removal Tool

Lazer is an open-source Python tool designed to remove direct messages (DMs) on Discord efficiently. Built with a PyQt6 interface, it provides an easy way to bulk-delete messages.

Features:

Bulk delete DMs on Discord

Simple and user-friendly GUI

Uses Discord API requests for message deletion


Installation

Requirements:

Ensure you have Python installed. Then, install the required dependencies:

pip install -r requirements.txt


Dependencies

Lazer requires the following Python libraries:

pip install PyQt6 requests


Usage

Run the tool with:

python lazer.py

Enter your Discord token and the channel ID of the DM you want to clean.

Start the deletion process and let the tool handle the rest.


Getting Your Discord Token:


Method: Using Network Requests

Open Discord in your browser.

Press Ctrl + Shift + I (Windows/Linux) or Cmd + Option + I (Mac) to open Developer Tools.

Navigate to the Network tab.

In the search bar, type messages.

Send a message in any DM or server.

Click on any messages request, go to the Headers tab.

Scroll down to find the authorization header—this is your token.

⚠ Warning: Never share your token, as it grants full access to your account.



Getting a DM Channel ID:


Method: Enable Developer Mode & Copy Channel ID

Open Discord and go to User Settings.

Scroll down to Advanced and enable Developer Mode.

Go to the DM you want to delete messages from.

Right-click the conversation in the left sidebar.

Click Copy Channel ID.



License

This project is open-source under the MIT License.



Contributions

Feel free to contribute by submitting pull requests or reporting issues!
