import os


class DiscordBot:
    token = os.environ["TOKEN"]
    cogs = [
        "cogs.admin",
        "cogs.report",
        "cogs.streaming"
    ]

