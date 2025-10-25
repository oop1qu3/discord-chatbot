import os
import copy
import time
from dotenv import load_dotenv
from google.genai import Client
from modules.injection import Injection
from constants import *

class TextLLMWrapper:
    def __init__(self, signals, modules=None) -> None:
        self.signals = signals
        self.modules = modules

        self.client = self._initialize_gemini_client()
    
    def _initialize_gemini_client(self):
        try:
            load_dotenv()
            client = Client(api_key=os.getenv("GEMINI_API_KEY"))
            self.signals.logger.info("Gemini Client 초기화 성공.")
            return client
        except Exception as e:
            self.signals.logger.info(f"Gemini Client 초기화 오류: {e}")
            return None
    
    # Assembles all the injections from all modules into a single prompt by increasing priority
    def assemble_injections(self, injections=None):
        if injections is None:
            injections = []

        # Gather all injections from all modules
        for module in self.modules.values():
            injections.append(module.get_prompt_injection())

        # Let all modules clean up once the prompt injection has been fetched from all modules
        for module in self.modules.values():
            module.cleanup()

        # Sort injections by priority
        injections = sorted(injections, key=lambda x: x.priority)

        # Assemble injections
        prompt = ""
        for injection in injections:
            prompt += injection.text
        return prompt
    
    def generate_prompt(self):
        messages = copy.deepcopy(self.signals.history)

        # For every message prefix with speaker name unless it is blank
        for message in messages:
            if message["role"] == "user" and message["content"] != "":
                message["content"] = HOST_NAME + ": " + message["content"] + "\n"
            elif message["role"] == "assistant" and message["content"] != "":
                message["content"] = AI_NAME + ": " + message["content"] + "\n"

        while True:
            chat_section = ""
            for message in self.signals.recentDiscordMessages:
                chat_section += (message + "\n")
            generation_prompt = ""

            base_injections = [Injection(chat_section, 100)]
            middle_prompt = chat_section + "\n" + MIDDLE_PROMPT

            middle_response = self.client.models.generate_content(
                model='gemini-2.0-flash',
                contents=middle_prompt, 
            )

            full_prompt = chat_section + "\n" + middle_response.text + "\n" + PROMPTER_PROMPT
            self.signals.logger.debug("full_prompt:" + "\n" + full_prompt) 

            return full_prompt  # FIXME
            '''wrapper = [{"role": "user", "content": full_prompt}]

            # Find out roughly how many tokens the prompt is
            # Not 100% accurate, but it should be a good enough estimate
            prompt_tokens = len(self.tokenizer.apply_chat_template(wrapper, tokenize=True, return_tensors="pt")[0])
            # print(prompt_tokens)

            # Maximum 90% context size usage before prompting LLM
            if prompt_tokens < 0.9 * self.CONTEXT_SIZE:
                self.signals.sio_queue.put(("full_prompt", full_prompt))
                # print(full_prompt)
                return full_prompt
            else:
                # If the prompt is too long even with no messages, there's nothing we can do, crash
                if len(messages) < 1:
                    raise RuntimeError("Prompt too long even with no messages")

                # Remove the oldest message from the prompt and try again
                messages.pop(0)
                print("Prompt too long, removing earliest message")'''
    
    def prepare_payload(self):
        return [{
            "role": "user",
            "parts": [{"text": self.generate_prompt()}] 
        }]
    
    def prompt(self):
        self.signals.AI_thinking = True

        time.sleep(1)
        data = self.prepare_payload()

        response = self.client.models.generate_content(
            model='gemini-2.0-flash',
            contents=data, 
        )

        if response.text[0] == 'o':
            AI_message = response.text[2:-2]
            self.signals.AI_message = AI_message
            self.signals.send_now = True
        
        self.signals.logger.debug("response:" + "\n" + response.text)

        self.signals.AI_thinking = False