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
    load_dotenv()
    
    # configure root logger
    logging.basicConfig(
        level=logging.DEBUG, 
        format='%(asctime)s [%(levelname)s] %(name)s - %(message)s', 
        #filename="Neurorong.log",
        #filemode="w"
    )
    logger = logging.getLogger('main')
    logger.info("고성능 최신 챗봇, 뉴로롱 로딩 증..")

    # Register signal handler so that all threads can be exited.
    def signal_handler(sig, frame):
        logger.debug('Received CTRL + C, attempting to gracefully exit. Close all dashboard windows to speed up shutdown.')
        signals.terminate = True

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Singleton object that every module will be able to read/write to
    signals = Signals()

    # MODULES
    # Modules that start disabled CANNOT be enabled while the program is running.
    modules = {}
    module_threads = {}

    # Create LLMWrappers
    llm = TextLLMWrapper(signals, modules)

    # Create Prompter
    prompter = Prompter(llm, signals, modules)

    # Create Discord bot
    modules['discord'] = DiscordClient(signals, enabled=True)
    # Create Memory module
    modules['memory'] = Memory(signals, enabled=True)

    # Set discord message history
    llm.setMessageHistory(modules['discord'].message_history)
    prompter.setMessageHistory(modules['discord'].message_history)
    modules['memory'].setMessageHistory(modules['discord'].message_history)

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
    prompter_thread.join()
    logger.info("PROMPTER EXITED ======================")

    # Wait for all modules to finish
    for module_thread in module_threads.values():
        module_thread.join()
    logger.info("MODULES EXITED ======================")

    logger.info("All threads exited, shutdown complete")
    sys.exit(0)

if __name__ == '__main__':
    asyncio.run(main())

