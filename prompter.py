import time
import asyncio

class Prompter:
    def __init__(self, signals, llm, modules=None):
        self.signals = signals
        self.llm = llm
        if modules is None:
            self.modules = {}
        else:
            self.modules = modules

        self.system_ready = False
        self.timeSinceLastMessage = 0.0
    
    def prompt_now(self):
        # Don't prompt AI if ai is thinking
        if self.signals.AI_thinking:
            return False
        
        if not self.signals.online:
            return False
        
        if self.signals.on_message:
            return True

    def prompt_loop(self):
        self.signals.logger.info("Prompter started")

        while not self.signals.terminate:
            if self.prompt_now():
                self.llm.prompt()
                self.signals.on_message = False

                time.sleep(2)