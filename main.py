import asyncio
import os
import time
import threading
import sys
import signal
import logging

from dotenv import load_dotenv
from google.genai import Client

from signals import Signals
from modules.discordClient import DiscordClient
from llmWrappers.textLLMWrapper import TextLLMWrapper
from prompter import Prompter
from modules.memory import Memory
from constants import *

async def main():
    # Create logger 
    logger = logging.getLogger('my_discord_bot')
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO) 
    file_handler = logging.FileHandler(filename="Neurorong.log", encoding="utf-8", mode="w")
    file_handler.setLevel(logging.DEBUG) 
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    try:
        load_dotenv()
        client = Client(api_key=os.getenv("GEMINI_API_KEY"))
        logger.info("Gemini Client 초기화 성공.")
    except Exception as e:
        logger.info(f"Gemini Client 초기화 오류: {e}")

    logger.info("고성능 최신 챗봇, 뉴로롱 로딩 증..")

    # Register signal handler so that all threads can be exited.
    def signal_handler(sig, frame):
        logger.debug('Received CTRL + C, attempting to gracefully exit. Close all dashboard windows to speed up shutdown.')
        signals.terminate = True

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Singleton object that every module will be able to read/write to
    signals = Signals()
    signals.logger = logger
    signals.client = client

    # MODULES
    # Modules that start disabled CANNOT be enabled while the program is running.
    modules = {}
    module_threads = {}

    # Create LLMWrappers
    llm = TextLLMWrapper(signals, modules)

    # Create Prompter
    prompter = Prompter(signals, llm, modules)

    # Create Discord bot
    modules['discord'] = DiscordClient(signals, enabled=True)
    # Create Memory module
    modules['memory'] = Memory(signals, enabled=True)

    # Create threads (As daemons, so they exit when the main thread exits)
    prompter_thread = threading.Thread(target=prompter.prompt_loop, daemon=True)
    # Start Threads
    prompter_thread.start()

    # Create and start threads for modules
    for name, module in modules.items():
        module_thread = threading.Thread(target=module.init_event_loop, daemon=True)
        module_threads[name] = module_thread
        module_thread.start()

    while not signals.terminate:
        time.sleep(0.1)
    logger.info("TERMINATING ======================")

    # Wait for child threads to exit before exiting main thread

    # Wait for all modules to finish
    for module_thread in module_threads.values():
        module_thread.join()
    logger.info("MODULES EXITED ======================")

    prompter_thread.join()
    logger.info("PROMPTER EXITED ======================")

    logger.info("All threads exited, shutdown complete")
    sys.exit(0)

if __name__ == '__main__':
    asyncio.run(main())

