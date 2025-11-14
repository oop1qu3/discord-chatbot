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

            # output += "Pick the highest quality message with the most potential" \
            #     " for an interesting answer and respond to them. output only response with no explanation\n"
            self.prompt_injection.text = output
        else:
            self.prompt_injection.text = ""
        return self.prompt_injection

    def cleanup(self):
        # Clear out handled discord messages
        # self.signals.recentDiscordMessages = []  

        return  # currently disenabled


    async def run(self):
        self.signals.logger.info("Discord bot started")

        load_dotenv()
        # TOKEN = os.getenv('DISCORD_TOKEN')
        TOKEN = os.getenv('TEST_DISCORD_TOKEN')
        
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
            self.signals.logger.info(f"DISCORD: Bot is ready for work")

            await self.bot.change_presence(status=discord.Status.online, activity=discord.Game("!전원 on/off | 수다 떨기"))
        
        # this will be called whenever a message in a channel was send by either the bot OR another user
        @bot.event
        async def on_message(message: discord.Message):
            if not self.enabled:
               return

            if len(message.content) > DISCORD_MAX_MESSAGE_LENGTH:
                return

            self.signals.logger.debug(f'in #{message.channel.name} | {message.channel.guild.name}, {message.author.display_name} said: {message.content}')
            # Store the 100 most recent chat messages
            if len(self.signals.recentDiscordMessages) > 100:
                self.signals.recentDiscordMessages.pop(0)
            self.signals.recentDiscordMessages.append(f"[{message.author.display_name} : {message.content}]")

            # Set recentDiscordMessages to itself to trigger the setter (updates frontend)
            self.signals.recentDiscordMessages = self.signals.recentDiscordMessages
            
            # save recent channel
            self.signals.recentChannel = message.channel

            if message.content.startswith('!'):
                await bot.process_commands(message) 
                return

            # save host's message
            # if message.author.display_name == HOST_NAME:
            #     self.signals.history.append({"role": "user", "content": message.content})
            
            # prompt when user sends discord message
            if not message.author.bot and self.signals.online:
                self.signals.on_message = True

        @bot.command(aliases=['전원'])
        async def power(ctx, status: str):
            self.signals.logger.debug("command on")
            if status.lower() == "on":
                if not self.signals.online:
                    await ctx.send("안녕! 나 불렀어?")
                    self.signals.online = True   

            elif status.lower() == "off":
                if self.signals.online:
                    await ctx.send("뉴로롱은 더 이상 얘기하지 않아요, 안녕!")
                    self.signals.online = False

            else:
                await ctx.send("[system] 잘못된 옵션: 'on' 또는 'off'만 입력하세요")
            
        @bot.command(aliases=['기억출력'])
        async def print_memory(ctx):
            all_memories = self.signals.API.get_memories()
            self.signals.logger.debug("--- 모든 저장된 메모리 목록 ---")
            for memory in all_memories:
                self.signals.logger.debug(f"ID: {memory['id']}")
                self.signals.logger.debug(f"Document: {memory['document'][:80]}...") # 내용이 길면 일부만 출력
                self.signals.logger.debug(f"Metadata: {memory['metadata']}")
                self.signals.logger.debug("-" * 20)

        @bot.command(aliases=['기억삭제'])
        async def delete_memory(ctx, id: str):
            self.signals.API.delete_memory(id)

        async def send_message():
            await self.bot.wait_until_ready()

            try:
                while not self.bot.is_closed():
                    if self.signals.send_now: 
                        if self.signals.recentChannel:
                            await asyncio.sleep(3)
                            try:
                                await self.signals.recentChannel.send(self.signals.AI_message)
                                
                                await asyncio.sleep(2)
                                self.signals.send_now = False
                                    
                            except Exception as e:
                                self.signals.logger.info(f"Error sending Discord message: {e}")
                    
                    await asyncio.sleep(0.1)
            except CancelledError:
                self.signals.logger.info("DISCORD: Background sender loop successfully terminated by external signal.")
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
                self.signals.logger.info("DISCORD: Bot connection closed unexpectedly.")
                return

            await asyncio.sleep(0.1)

