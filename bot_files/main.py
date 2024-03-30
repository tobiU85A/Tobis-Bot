import discord
import os
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True

load_dotenv("tobis_lab_bot.env")

bot = discord.Bot(
    intents=intents,
    debug_guilds=[os.getenv("DC_ID")]
)

# Prints a message to the console if the bot is online.
client = discord.Client()


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}.')

# Automatically loads the cogs.
rootDir = "cogs"

for subdir, dirs, files in os.walk(rootDir):
    for fileName in files:
        filepath = os.path.join(subdir, fileName)

        if filepath.endswith(".py"):
            # Convert path to module format (replace os separator with dots)
            cog_module = os.path.splitext(filepath.replace(os.path.sep, '.'))[0]

            # Convert the module to a relative import path
            import_path = cog_module
            bot.load_extension(import_path)

bot.run(os.getenv("BOT_TOKEN"))

