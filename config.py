import os
from dotenv import load_dotenv

load_dotenv()


class DiscordBot:
    token = os.environ["TOKEN"]
    cogs = [
        "cogs.admin",
        "cogs.report",
        "cogs.streaming"
    ]

