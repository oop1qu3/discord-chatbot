import asyncio
import time
import threading
import sys
import signal

from signals import Signals
from modules.discord.discordBot import DiscordBot
from modules.discord.discordClient import DiscordClient
from llmWrappers.textLLMWrapper import TextLLMWrapper
from prompter import Prompter

async def main():

    print("고성능 최신 챗봇, 뉴로롱 로딩 증..")

    # Register signal handler so that all threads can be exited.
    def signal_handler(sig, frame):
        print('Received CTRL + C, attempting to gracefully exit. Close all dashboard windows to speed up shutdown.')
        signals.terminate = True

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Singleton object that every module will be able to read/write to
    signals = Signals()

    # MODULES
    # Modules that start disabled CANNOT be enabled while the program is running.
    modules = {}

    # Create Discord bot
    discordBot = DiscordBot(signals)
    modules['discord'] = DiscordClient(discordBot, signals, enabled=True)

    # Create LLMWrappers
    llm = TextLLMWrapper(discordBot, signals)

    # Create Prompter
    prompter = Prompter(signals, llm, modules)

    # Create tasks
    prompt_task = asyncio.create_task(prompter.start())
    discord_bot_tasks = asyncio.create_task(modules['discord'].start_bot())
    discord_sender_tasks = asyncio.create_task(modules['discord'].start_sender())
    
    while not signals.terminate:
        await asyncio.sleep(1)

    print("TERMINATING ======================")

    # Wait for all tasks to finish
    await modules['discord'].close_bot() 
    await modules['discord'].close_sender()

    await discord_bot_tasks
    await discord_sender_tasks
    print("MODULES EXITED ======================")

    await prompter.close()
    await prompt_task
    print("PROMPTER EXITED ======================")

    print("All threads exited, shutdown complete")
    sys.exit(0)

if __name__ == '__main__':
    asyncio.run(main())

