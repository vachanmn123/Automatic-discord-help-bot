import datetime
import time
import requests
from flask import Flask, redirect, url_for, flash, render_template, request
from flask_discord import DiscordOAuth2Session, requires_authorization, Unauthorized
import json
import os

app = Flask(__name__)

config = json.load(open("web/config.json"))

app.secret_key = config["secret_key"]

if config["environment"] == "development":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true"

app.config["DISCORD_CLIENT_ID"] = config["discord_info"]["DISCORD_CLIENT_ID"]
app.config["DISCORD_CLIENT_SECRET"] = config["discord_info"]["DISCORD_CLIENT_SECRET"]
app.config["DISCORD_REDIRECT_URI"] = config["discord_info"]["DISCORD_REDIRECT_URI"]
app.config["DISCORD_BOT_TOKEN"] = config["discord_info"]["DISCORD_BOT_TOKEN"]
app.config["DISCORD_BOT_WEBHOOK_URL"] = config["discord_info"]["log_webhook"]

discord = DiscordOAuth2Session(app)


@app.route("/")
@requires_authorization
def index():
    user = discord.fetch_user()
    return render_template("index.html", user=user)


@app.route("/login")
def login():
    if discord.authorized:
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/discordredirect")
def discordredirect():
    if discord.authorized:
        return redirect(url_for("index"))
    return discord.create_session(scope="identify")


@app.route("/logout")
def logout():
    discord.revoke()
    flash("You have been logged out")
    return redirect(url_for("login"))


@app.route("/callback/")
def callback():
    discord.callback()
    user = discord.fetch_user()
    if not str(user.id) in config["allowed_user_ids"]:
        discord.revoke()
        flash("You are not allowed to use this feature.")
        return redirect(url_for("login"))
    data = {
        "username": user.name,
        "avatar_url": user.avatar_url,
        "embeds": [
            {
                "title": "User Logged in",
                "description": f"{user.name} ({user.id}) logged in.",
                "timestamp": str(datetime.datetime.utcfromtimestamp(time.time())),
                "color": 0x00FF00,
            }
        ],
        "content": "User Logged in",
    }
    resp = requests.post(config["discord_info"]["log_webhook"], json=data)
    print(resp.status_code, resp.reason, resp.text)
    return redirect(url_for("index"))


@app.route("/addnewresponder", methods=["POST", "GET"])
@requires_authorization
def addnewresponder():
    if request.method == "POST":
        data = request.form
        final_json = {
            "name": data["name"],
            "description": data["description"],
            "author": data["author"],
            "response": data["response"],
            "keywords": [],
            "media_links": [],
        }
        for keyword in data["triggers"].split("\n"):
            final_json["keywords"].append(keyword.replace("\r", ""))
        for media_link in data["medialinks"].split("\n"):
            final_json["media_links"].append(media_link.replace("\r", ""))
        with open(f"responses/{final_json['name'].replace(' ', '')}.json", "w") as f:
            f.write(json.dumps(final_json, indent=4))
        data = {
            "username": discord.fetch_user().name,
            "author_url": discord.fetch_user().avatar_url,
            "embeds": [
                {
                    "title": "New Responder Added",
                    "description": f"{final_json['name']} has been added by {discord.fetch_user().name}.",
                    "author": {
                        "name": discord.fetch_user().name,
                        "url": discord.fetch_user().avatar_url,
                    },
                }
            ],
            "files": {},
        }
        resp = requests.post(config["discord_info"]["log_webhook"], json=data)
        with open(f"responses/{final_json['name'].replace(' ', '')}.json") as f:
            data["files"][f"_{final_json['name'].replace(' ', '')}.json"] = (
                f"{final_json['name'].replace(' ', '')}.json",
                f.read(),
            )
        data["payload_json"] = (None, json.dumps(data))
        resp = requests.post(config["discord_info"]["log_webhook"], files=data["files"])
        return redirect(url_for("index"))
    return render_template("addnewresponder.html")


@app.route("/viewallresponders")
@requires_authorization
def viewallresponders():
    responders = []
    for file in os.listdir("responses"):
        if file.endswith(".json"):
            with open(f"responses/{file}", "r") as f:
                responders.append(json.load(f))
    return render_template("viewallresponders.html", responders=responders)


@app.errorhandler(Unauthorized)
def unauthorized(e):
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
