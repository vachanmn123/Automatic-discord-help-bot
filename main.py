from email import message
import disnake
from disnake.ext import commands
import logging
import json
from datetime import datetime

# Setup gateway intents
intents = disnake.Intents.default()
intents.message_content = True
intents.members = True

# Setup discord client
bot = commands.Bot(
    command_prefix=json.load(open("config.json"))["bot_prefix"], intents=intents
)

# Setup disnake logging
logger = logging.getLogger("disnake")
if json.load(open("config.json"))["development"]:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
handler = logging.FileHandler(
    filename=f"logs/IvyBot-{datetime.now().isoformat()}.log",
    encoding="utf-8",
    mode="w",
)
consoleHandler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
consoleHandler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)
logger.addHandler(consoleHandler)
bot.logger = logger

# Load cogs
bot.load_extension("cogs.autoResponder")


@bot.event
async def on_ready():
    return bot.logger.info(f"Logged in as {bot.user.name}")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)


@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")


# Run the bot
bot.run(json.load(open("config.json"))["bot_token"])
