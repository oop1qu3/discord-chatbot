import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord.ext.commands import Context
import logging
import asyncio
from asyncio import CancelledError

from modules.module import Module
from constants import *

class DiscordClient(Module):
    def __init__(self, signals, enabled=True):
        super().__init__(signals, enabled)

        self.bot = None
        self.message_history = []
        self.current_channel = ""

        self.logger = logging.getLogger("DiscordClient")

    def cleanup(self):
        # Clear out handled discord messages
        # self.signals.recentDiscordMessages = []  

        return  # currently disenabled


    async def run(self):
        self.logger.info("Discord bot started")

        load_dotenv()
        TOKEN = os.getenv('DISCORD_TOKEN')
        #TOKEN = os.getenv('TEST_DISCORD_TOKEN')
        
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
            help_command=None,
            activity=discord.Game("봇 로딩"),
        )

        # also save bot to class properties so we can shut them down
        self.bot = bot

        # this will be called when the event READY is triggered, which will be on bot start
        @bot.event
        async def on_ready():
            self.logger.info(f"DISCORD: Bot is ready for work")

            await self.bot.change_presence(status=discord.Status.online, activity=discord.Game("!도움 | 수다 떨기"))
        
        # this will be called whenever a message in a channel was send by either the bot OR another user
        @bot.event
        async def on_message(message: discord.Message):
            if not self.enabled:
                return

            if len(message.content) > DISCORD_MAX_MESSAGE_LENGTH:
                return

            #self.logger.debug(f'in #{message.channel.name} | {message.channel.guild.name}, {message.author.display_name}: {message.content}')
            self.message_history.append(f"[{message.author.display_name}: {message.content}]")
            # Store the 100 most recent chat messages
            if len(self.message_history) > 100:
                self.message_history.pop(0)

            if message.content.startswith('!'):
                await bot.process_commands(message) 
                return
            
            # prompt when user sends discord message
            if not message.author.bot and self.signals.online:
                self.signals.on_message = True

        @bot.command(aliases=['도움'])
        async def help(ctx: Context):
            await ctx.send("- `!도움`: 명령어 목록을 출력해요\n- `!전원 on/off`: 뉴로롱의 전원을 조작해요\n- `!채널설정`: 뉴로롱과 이야기할 채널을 설정해요")

        @bot.command(aliases=['전원'])
        async def power(ctx: Context, status: str = None):
            if not self.current_channel:
                await ctx.send("채널이 설정되어 있지 않아 뉴로롱의 전원을 조작할 수 없어요. 채널을 설정하려면 `!채널설정`을 입력해주세요!")
                return
            elif ctx.channel != self.current_channel:
                await ctx.send("채널이 달라 뉴로롱의 전원을 조작할 수 없어요. 채널 설정을 변경하려면 `!채널설정`을 입력해주세요!")
                return
            
            if status.lower() == "on":
                if not self.signals.online:
                    await ctx.send("안녕! 나 불렀어?")
                    self.signals.online = True

            elif status.lower() == "off":
                if self.signals.online:
                    await ctx.send("뉴로롱은 더 이상 얘기하지 않아요, 안녕!")
                    self.signals.online = False

            else:
                await ctx.send("잘못된 옵션입니다. `on` 또는 `off`를 입력하세요!")
        
        @bot.command(aliases=['채널설정'])
        async def setCurrentChannel(ctx: Context):
            self.current_channel = ctx.channel
            await ctx.send(f"뉴로롱은 이제 `#{ctx.channel.name}`에서 이야기해요!")
            
        @bot.command(aliases=['기억출력'])
        async def print_memory(ctx: Context):
            all_memories = self.signals.API.get_memories()
            self.logger.debug("--- 모든 저장된 메모리 목록 ---")
            for memory in all_memories:
                self.logger.debug(f"ID: {memory['id']}")
                self.logger.debug(f"Document: {memory['document'][:80]}...") # 내용이 길면 일부만 출력
                self.logger.debug(f"Metadata: {memory['metadata']}")
                self.logger.debug("-" * 20)

        @bot.command(aliases=['기억삭제'])
        async def delete_memory(ctx: Context, id: str):
            self.signals.API.delete_memory(id)

        async def send_message():
            await self.bot.wait_until_ready()

            try:
                while not self.bot.is_closed():
                    if not self.signals.send_now:
                        await asyncio.sleep(0.1) 
                        continue

                    if not self.current_channel:
                        await asyncio.sleep(0.1)
                        continue
                    
                    try:
                        for frag in self.signals.fragmented_response:
                            length = len(frag)
                            calculated_delay = MIN_SLEEP_TIME + (length * CHAR_DELAY_FACTOR)
                            sleep_duration = min(calculated_delay, MAX_SLEEP_TIME)

                            await self.current_channel.send(frag)
                            await asyncio.sleep(sleep_duration)

                            if self.signals.on_message:
                                break
                        
                        self.signals.send_now = False
                            
                    except Exception as e:
                        self.logger.info(f"Error sending Discord message: {e}")
                
                    await asyncio.sleep(0.1)
            except CancelledError:
                self.logger.info("DISCORD: Background sender loop successfully terminated by external signal.")
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
                self.logger.info("DISCORD: Bot connection closed unexpectedly.")
                return

            await asyncio.sleep(0.1)

