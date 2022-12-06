#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import traceback
import discord
from discord.ext import commands
from config import DiscordBot
import cogs.streaming as streaming

intent = discord.Intents.all()


class Morrigan(commands.Bot):
    def __init__(self, **kwargs):
        intents = discord.Intents.all()
        super().__init__(command_prefix=commands.when_mentioned_or('$'), intents=intents, **kwargs, pm_help=None,
                         help_attrs=dict(hidden=True))

    async def setup_hook(self) -> None:
        self.add_view(streaming.StreamingManagementPanel())
        for extension in DiscordBot.cogs:
            try:
                await self.load_extension(extension)
            except Exception as e:
                print('Could not load extension {0} due to {1.__class__.__name__}: {1}'.format(
                    extension, e))
        await self.tree.sync()

    async def on_ready(self):
        print('Logged on as {0} (ID: {0.id})'.format(self.user))

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            return

        orig_error = getattr(error, "original", error)
        error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
        error_msg = "```py\n" + error_msg + "\n```"
        await ctx.send(error_msg)


bot = Morrigan()


@bot.tree.context_menu(name='メッセージを報告する')
async def report_message(interaction: discord.Interaction, message: discord.Message):
    await interaction.response.send_message(
        f'{message.author.mention}によるメッセージをモデレータに対し報告を行いました。', ephemeral=True
    )

    log_channel = interaction.guild.get_channel(1048172287817416744)

    embed = discord.Embed(title='報告が行われました')
    if message.content:
        embed.description = message.content

    embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
    embed.timestamp = message.created_at

    url_view = discord.ui.View()
    url_view.add_item(discord.ui.Button(label='メッセージへ', style=discord.ButtonStyle.url, url=message.jump_url))

    await log_channel.send(embed=embed, view=url_view)


bot.run(DiscordBot.token)
