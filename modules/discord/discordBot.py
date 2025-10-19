import discord
from discord.ext import commands
import asyncio
import random

from prompter import Prompter

intents = discord.Intents(
    message_content=True, 
    members=True, 
    guilds=True, 
    emojis=True, 
    messages=True, 
    reactions=True, 
    typing=True
)

class DiscordBot(commands.Bot):
    def __init__(self, signals) -> None:
        super().__init__(
            command_prefix="!",
            intents=intents,
            activity=discord.Game("봇 로딩"),
        )

        self.signals = signals 

    async def update_presence(self) -> None:
        await self.change_presence(status=discord.Status.online, activity=discord.Game("수다 떨기"))

    # @Override
    async def on_ready(self):
        print(f"로그인 성공: {self.user.name} (ID: {self.user.id})")

        await self.update_presence()

    # @Override
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        
        await self.signals.message_queue_in.put(message)
        print(f"> 받은 메시지: {message.content}")

