import asyncio
import time
import threading
import sys
import signal

from signals import Signals
from modules.discordClient import DiscordClient
from llmWrappers.textLLMWrapper import TextLLMWrapper
from prompter import Prompter
from modules.memory import Memory

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
    module_threads = {}

    # Create LLMWrappers
    llm = TextLLMWrapper(signals, modules)

    # Create Prompter
    prompter = Prompter(signals, llm, modules)

    # Create Discord bot
    modules['discord'] = DiscordClient(signals, enabled=True)
    # Create Memory module
    # modules['memory'] = Memory(signals, enabled=True)

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
    print("TERMINATING ======================")

    # Wait for child threads to exit before exiting main thread

    # Wait for all modules to finish
    for module_thread in module_threads.values():
        module_thread.join()
    print("MODULES EXITED ======================")

    prompter_thread.join()
    print("PROMPTER EXITED ======================")

    print("All threads exited, shutdown complete")
    sys.exit(0)

if __name__ == '__main__':
    asyncio.run(main())

