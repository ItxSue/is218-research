"""Flash Tap account and private result slice."""
import os
import secrets
import sqlite3
from pathlib import Path
from flask import Flask, abort, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


def create_app(database=None):
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    app.config.update(DATABASE=str(database or Path(app.instance_path)/"flash.sqlite3"),
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(app.config["DATABASE"]) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS results(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, milliseconds INTEGER NOT NULL, round_id TEXT UNIQUE NOT NULL);
        """)

    @app.before_request
    def csrf():
        session.setdefault("csrf", secrets.token_hex(32))
        if request.method == "POST" and not secrets.compare_digest(request.form.get("csrf", ""), session["csrf"]):
            abort(400, "Reload and try again.")

    @app.route("/<action>", methods=["GET", "POST"])
    def account(action):
        if action not in {"signup", "signin"}:
            abort(404)
        error = None
        if request.method == "POST":
            username = request.form.get("username", "").strip().lower()
            password = request.form.get("password", "")
            if not 3 <= len(username) <= 40 or not 10 <= len(password) <= 128:
                error = "Use a username of 3–40 characters and a password of 10–128 characters."
            else:
                with sqlite3.connect(app.config["DATABASE"]) as db:
                    if action == "signup":
                        try:
                            db.execute("INSERT INTO users(username,password) VALUES (?,?)", (username, generate_password_hash(password)))
                        except sqlite3.IntegrityError:
                            error = "Choose another username."
                    user = db.execute("SELECT id,password FROM users WHERE username=?", (username,)).fetchone()
                if not error and user and check_password_hash(user[1], password):
                    session.clear()
                    session.update(user_id=user[0], csrf=secrets.token_hex(32))
                    return redirect(url_for("game"))
                error = error or "Check your username and password."
        return render_template("account.html", action=action, error=error), 400 if error else 200

    @app.get("/")
    def game():
        if "user_id" not in session:
            return redirect(url_for("account", action="signin"))
        session["round_id"] = secrets.token_hex(24)
        with sqlite3.connect(app.config["DATABASE"]) as db:
            results = db.execute("SELECT milliseconds FROM results WHERE user_id=? ORDER BY id DESC LIMIT 20", (session["user_id"],)).fetchall()
        return render_template("game.html", results=results)

    @app.post("/result")
    def save_result():
        if "user_id" not in session:
            abort(401)
        try:
            milliseconds = int(request.form.get("milliseconds", ""))
        except ValueError:
            abort(422)
        if not 1 <= milliseconds <= 60000:
            abort(422)
        round_id = request.form.get("round_id", "")
        if not secrets.compare_digest(round_id, session.get("round_id", "")) or not round_id:
            abort(409)
        with sqlite3.connect(app.config["DATABASE"]) as db:
            try:
                db.execute("INSERT INTO results(user_id,milliseconds,round_id) VALUES (?,?,?)", (session["user_id"], milliseconds, round_id))
            except sqlite3.IntegrityError:
                abort(409)
        session.pop("round_id", None)
        return redirect(url_for("game"))

    @app.post("/signout")
    def signout():
        session.clear()
        return redirect(url_for("account", action="signin"))

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=int(os.environ.get("PORT", "5053")))
