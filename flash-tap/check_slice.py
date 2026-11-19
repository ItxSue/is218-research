"""Check accounts, result ownership, replay protection and persistence."""
import re
import sqlite3
import tempfile
from pathlib import Path
from app import create_app


def token(page, name):
    return re.search(('name="' + name + '" value="([^"]+)"').encode(), page.data)[1].decode()


with tempfile.TemporaryDirectory() as directory:
    database = Path(directory)/"flash.sqlite3"
    app = create_app(database)
    client = app.test_client()
    page = client.get("/signup")
    assert client.post("/signup", data=dict(csrf=token(page, "csrf"), username="alice", password="a-long-password"), follow_redirects=True).status_code == 200
    page = client.get("/")
    result = dict(csrf=token(page,"csrf"), round_id=token(page,"round_id"), milliseconds="245", user_id="999")
    assert client.post("/result", data=result | dict(milliseconds="-1")).status_code == 422
    assert client.post("/result", data=result).status_code == 302
    assert client.post("/result", data=result).status_code == 409
    assert b"245 ms" in client.get("/").data
    page = client.get("/")
    assert client.post("/signout", data=dict(csrf=token(page,"csrf"))).status_code == 302
    assert client.get("/").status_code == 302
    other = app.test_client()
    page = other.get("/signup")
    other.post("/signup", data=dict(csrf=token(page,"csrf"), username="bobby", password="another-password"))
    assert b"245 ms" not in other.get("/").data
    restarted = create_app(database).test_client()
    page = restarted.get("/signin")
    signed = restarted.post("/signin", data=dict(csrf=token(page,"csrf"), username="alice", password="a-long-password"), follow_redirects=True)
    assert b"245 ms" in signed.data
    with sqlite3.connect(database) as db:
        assert db.execute("SELECT user_id FROM results").fetchone()[0] == 1
        assert db.execute("SELECT password FROM users WHERE id=1").fetchone()[0] != "a-long-password"
    print("PASS — signup, signin, signout, saved result, input validation, replay, ownership, hashing and restart persistence")
