import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import logging
import asyncio
from asyncio import CancelledError

from modules.module import Module
from constants import *

class DiscordClient(Module):
    def __init__(self, signals, enabled=True):
        super().__init__(signals, enabled)

        self.bot = None
        self.prompt_injection.priority = 150

    def get_prompt_injection(self):
        if len(self.signals.recentDiscordMessages) > 0:
            output = "\nThese are recent discord messages:\n"
            for message in self.signals.recentDiscordMessages:
                output += message + "\n"

            output += "Pick the highest quality message with the most potential" \
                " for an interesting answer and respond to them. output only response with no explanation\n"
            self.prompt_injection.text = output
        else:
            self.prompt_injection.text = ""
        return self.prompt_injection

    def cleanup(self):
        # Clear out handled discord messages
        self.signals.recentDiscordMessages = []


    async def run(self):
        print("Discord bot started")
        # handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")

        load_dotenv()
        TOKEN = os.getenv('DISCORD_TOKEN')
        
        intents = discord.Intents(
            message_content=True, 
            members=True, 
            guilds=True, 
            emojis=True, 
            messages=True, 
            reactions=True, 
            typing=True
        )

        # create bot
        bot = commands.Bot(
            command_prefix="!", 
            intents=intents, 
            activity=discord.Game("봇 로딩"),
        )

        # also save bot to class properties so we can shut them down
        self.bot = bot

        # this will be called when the event READY is triggered, which will be on bot start
        @bot.event
        async def on_ready():
            print(f"DISCORD: Bot is ready for work")

            await self.bot.change_presence(status=discord.Status.online, activity=discord.Game("수다 떨기"))
        
        # this will be called whenever a message in a channel was send by either the bot OR another user
        @bot.event
        async def on_message(message: discord.Message):
            if not self.enabled:
               return

            if len(message.content) > DISCORD_MAX_MESSAGE_LENGTH:
                return

            print(f'in #{message.channel.name} | {message.channel.guild.name}, {message.author.display_name} said: {message.content}')
            # Store the 10 most recent chat messages
            if len(self.signals.recentDiscordMessages) > 10:
                self.signals.recentDiscordMessages.pop(0)
            self.signals.recentDiscordMessages.append(f"[{message.author.display_name} : {message.content}]")

            # Set recentDiscordMessages to itself to trigger the setter (updates frontend)
            self.signals.recentDiscordMessages = self.signals.recentDiscordMessages
            
            # save recent channel
            self.signals.recentChannel = message.channel

            # save host's message
            if message.author.display_name == HOST_NAME:
                self.signals.history.append({"role": "user", "content": message.content})
            
            # prompt when user sends discord message
            if not message.author.bot:
                self.signals.on_message = True
            
        async def send_message():
            # 봇이 완전히 준비될 때까지 기다립니다.
            await self.bot.wait_until_ready()
            
            process_count = 0

            try:
                while not self.bot.is_closed():
                    if len(self.signals.history) - process_count > 0: 
                        # 리스트가 비어 있지 않다면, 마지막 요소에 안전하게 접근합니다.
                        if self.signals.history[-1]["role"] == "assistant":
        
                            # 🚨 채널이 설정되었는지도 확인하는 것이 안전합니다.
                            if self.signals.recentChannel:
                                try:
                                    ai_message = self.signals.history[-1]["content"]
                                    await self.signals.recentChannel.send(ai_message)
                                    
                                    process_count = len(self.signals.history)
                                    
                                except Exception as e:
                                    print(f"Error sending Discord message: {e}")
                    
                    # 리스트가 비어있거나 조건이 만족하지 않으면 0.5초 대기
                    await asyncio.sleep(5)
            except CancelledError:
                print("DISCORD: Background sender loop successfully terminated by external signal.")
                pass

        # Checkpoint to see if the bot is enabled
        if not self.enabled:
            return
        
        # we are done with our setup, lets start this bot up!
        bot_run_task = asyncio.create_task(self.bot.start(token=TOKEN))
        bot_send_task = asyncio.create_task(send_message())

        while True:
            if self.signals.terminate:
                await self.bot.close()
                bot_send_task.cancel()

                await bot_send_task
                await bot_run_task
                
                return
            
            if self.bot.is_closed():
                print("DISCORD: Bot connection closed unexpectedly.")
                return

            await asyncio.sleep(0.1)

