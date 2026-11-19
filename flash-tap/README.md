# Flash Tap — Review 2 first working slice

With Python 3.12, from this folder:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Open http://127.0.0.1:5053. Create a local practice account with a username and a password of at least 10 characters. Press Space or Enter on the round button to start, wait for TAP NOW, and press again. Save the result and sign out. Sign in again to see the saved attempt.

Run `.venv/bin/python check_slice.py` for the focused account and storage checks. Data is in the ignored instance folder. This is a loopback development app. Set a stable SECRET_KEY outside the process when persistent sessions are wanted.

The server owns user IDs and prevents duplicate saves of a round token. Browser measurements are user-controlled and intended for private practice. Server validation checks numeric bounds. It cannot certify a reaction time as tamper-proof.

Codex implemented and checked the first slice. The peer feedback in issue #1 covers the earlier written controls plan. A current human peer session on the working app is pending.

## Pattern experiment

The app factory pattern lets each focused check create an application with its own temporary database and simulate a new app instance. A module-global app and database path is simpler for startup but makes independent checks share state. Retain create_app(database) because the restart and account-isolation checks use separate stores and instances.
