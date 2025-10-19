import os
from dotenv import load_dotenv
import discord
from modules.module import Module
import modules.discord.discordBot as discordBot
import logging
import asyncio

class DiscordClient(Module):
    def __init__(self, bot, signals, enabled=True):
        super().__init__(signals, enabled)

        self.bot = bot 

    async def start_bot(self):
        print("Discord bot started")
        # handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")

        load_dotenv()
        await self.bot.start(token=os.getenv('DISCORD_TOKEN'))
    
    async def start_sender(self):
        while True:
            try:
                channel_id, content = await self.signals.message_queue_out.get() 

                if channel_id is None:
                    print("Sender Task: 종료 신호 감지. 루프 종료.")
                    break

                channel = self.bot.get_channel(channel_id)

                if channel:
                    await channel.send(content)
                    print(f"메시지 전송 완료 (채널: {channel_id})")
                
                self.signals.message_queue_out.task_done()
            except Exception as e:
                print(f"메시지 소비자 오류 발생: {e}")

                await asyncio.sleep(1)
    
    async def close_bot(self):
        await self.bot.close()

    async def close_sender(self):
        await self.signals.message_queue_out.put((None, None))
