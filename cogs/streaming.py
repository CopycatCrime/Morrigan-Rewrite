from typing import Any
import discord
from discord.ext import commands


class StatusCheck:
    def __init__(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.user = interaction.user

    async def is_in_voice_channel(self) -> bool:
        """配信に参加しているかどうかを判定します
        配信者であるかどうかの判定は行いません"""

        if not self.user.voice is None and self.user.voice.channel.category_id == 1044542086734696458:
            return True
        await self.interaction.response.send_message('配信に参加していないため操作を完了することができません。',
                                                     ephemeral=True, delete_after=15)
        return False

    async def is_streamer(self) -> bool:
        """配信者であるかどうかの判定を行います
        is_in_voice_channelの実行後の使用に限られます"""

        if self.user.voice.channel.overwrites_for(self.user).mute_members:
            return True
        await self.interaction.response.send_message('あなたはこのチャンネルの配信者でないためこの操作を完了することができません。',
                                                     ephemeral=True, delete_after=15)
        return False


class StreamingManagementFunctions:
    """実際に配信部屋に対し処理を行う関数"""

    def __init__(self, channel: discord.channel):
        self.channel = channel

    @staticmethod
    def overwrites(streamer: discord.member):
        """配信部屋のパーミッションを変更します"""

        overwrite = {streamer: discord.PermissionOverwrite(mute_members=True)}
        return overwrite

    async def change_streamer(self, streamer: discord.Member) -> None:
        """配信者を変更します
        配信者に対しロールを付与することで配信者と指定します"""

        await self.channel.edit(overwrites=self.overwrites(streamer))

    async def turn_off_auto_delete(self) -> None:
        """配信部屋の自動削除機能をオフにします"""
        # これを実行することで現状だと配信者がいなくなってしまう

        await self.channel.edit(overwrites={})

    async def rename_streaming(self, name: str):
        """配信部屋の名前を変更します"""

        await self.channel.edit(name=name)


class StreamingManagementPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='配信名変更', style=discord.ButtonStyle.grey,
                       custom_id='persistent_view:change_stream_name')
    async def change_stream_name(self, interaction: discord.Interaction, button: discord.ui.Button):
        """配信者が配信部屋の名前を変更します
        配信者でない人が操作するとエラーを返します"""

        if await StatusCheck(interaction).is_in_voice_channel() is True:
            await interaction.response.send_modal(RenameStreamingForum())

    @discord.ui.button(label='配信者変更', style=discord.ButtonStyle.grey, custom_id='persistent_view:change_streamer')
    async def change_streamer(self, interaction: discord.Interaction, button: discord.ui.Button):
        """配信者が配信者を変更します
        配信者でない人が操作をするとエラーを返します"""

        if await StatusCheck(interaction).is_in_voice_channel() is True:
            if await StatusCheck(interaction).is_streamer() is True:
                view = DropdownView(interaction.user.voice.channel.members)
                await interaction.response.send_message('次の配信者を選択してください:', view=view, ephemeral=True,
                                                        delete_after=15)

    @discord.ui.button(label='配信枠延長', style=discord.ButtonStyle.grey, custom_id='persistent_view:extend_streaming')
    async def extend_streaming(self, interaction: discord.Interaction, button: discord.ui.Button):
        """配信の枠を12時間延長します
        配信者でない人が操作するとエラーを返します"""

        if await StatusCheck(interaction).is_in_voice_channel() is True:
            await interaction.response.send_message('配信枠を12時間延長しました', ephemeral=True, delete_after=15)

    @discord.ui.button(label='自動削除解除', style=discord.ButtonStyle.grey,
                       custom_id='persistent_view:remove_function')
    async def remove_function(self, interaction: discord.Interaction, button: discord.ui.Button):
        """配信の自動削除機能をオフにします
        配信者でない人が操作するとエラーを返します"""

        if await StatusCheck(interaction).is_in_voice_channel() is True:
            await StreamingManagementFunctions(interaction.user.voice.channel).turn_off_auto_delete()
            await interaction.response.send_message('配信の自動削除機能を無効化しました', ephemeral=True, delete_after=15)


class Dropdown(discord.ui.Select):
    def __init__(self, members):
        options = []
        for member in members:
            options.append(
                discord.SelectOption(label=member.name, value=f"{member.id}", description=f'配信者を{member}に変更します'))

        super().__init__(placeholder='配信者を変更します', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        streamer = interaction.guild.get_member(int(self.values[0]))
        await StreamingManagementFunctions(interaction.user.voice.channel).change_streamer(streamer)
        await interaction.response.send_message(f'配信者を{streamer.mention}に変更しました', ephemeral=True, delete_after=15)


class DropdownView(discord.ui.View):
    def __init__(self, members):
        super().__init__()

        self.add_item(Dropdown(members))


class RenameStreamingForum(discord.ui.Modal, title='配信名を変更しようとしています...'):
    streaming_name = discord.ui.TextInput(label='配信名を入力してください')

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'配信名を{self.streaming_name}に変更します', ephemeral=True,
                                                delete_after=15)
        await StreamingManagementFunctions(interaction.user.voice.channel).rename_streaming(str(self.streaming_name))


class StreamingManagement(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @staticmethod
    def overwrites(streamer: discord.member):
        """配信部屋の権限を返します"""

        overwrite = {streamer: discord.PermissionOverwrite(mute_members=True)}
        return overwrite

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.member, before: discord.VoiceState,
                                    after: discord.VoiceState):

        create_streaming_channel: discord.channel = member.guild.get_channel(1044543110765613086)

        async def CreatingStreaming(streamer: discord.member):
            category_id = 1044542086734696458
            category = streamer.guild.get_channel(category_id)
            streaming_channel = await category.create_voice_channel(name=f"{streamer.display_name}",
                                                                    overwrites=self.overwrites(streamer))
            await streamer.move_to(streaming_channel)

        async def CloseStreamingChannel(listener: discord.member, streaming_channel: discord.channel):
            try:
                if streaming_channel.overwrites_for(listener).mute_members:
                    await streaming_channel.delete()
            except AttributeError:
                pass

        if before.channel is None:
            if after.channel == create_streaming_channel:
                await CreatingStreaming(member)
        else:
            if not before.channel.id == 1044543110765613086 and before.channel.category_id == 1044542086734696458:
                await CloseStreamingChannel(member, before.channel)

    @commands.command()
    @commands.is_owner()
    async def makeButton(self, ctx):
        embed = discord.Embed(title="配信情報変更パネル",
                              description="このメッセージの下にあるボタンを押すことで、自分の配信に限り配信の情報を変更することができます！ "
                                          "変更したい配信に接続したうえでボタンを押してください。自分が所有している配信でない場合はエラーとなります。",
                              color=0x00ff7f)
        embed.add_field(name="配信名変更", value="配信名を変更します", inline=True)
        embed.add_field(name="配信者変更", value="配信者を変更します", inline=True)
        embed.add_field(name="配信枠延長", value="配信の枠を更に12時間延長します", inline=False)
        embed.add_field(name="自動削除解除", value="配信者が切断した時の削除をキャンセルします(配信枠が終了した場合は削除されます)",
                        inline=True)
        embed.set_footer(text="配信情報変更パネル", icon_url=ctx.guild.icon)
        await ctx.channel.send(embed=embed, view=StreamingManagementPanel())


async def setup(bot):
    await bot.add_cog(StreamingManagement(bot))
