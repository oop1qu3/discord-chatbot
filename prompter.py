import logging
import time
import asyncio
from constants import *

class Prompter():
    def __init__(self, llm, signals, modules=None):
        self.llm = llm
        self.signals = signals
        if modules is None:
            self.modules = {}
        else:
            self.modules = modules

        self.logger = logging.getLogger("prompter")

        self.system_ready = False
        self.decider = Decider()
        self._message_history = []

    def setMessageHistory(self, message_history):
        self._message_history = message_history

    def prompt_now(self):
        # Don't prompt AI if ai is thinking
        if self.signals.AI_thinking:
            return False
        
        elif self.signals.send_now:
            return False
        
        elif self.signals.on_message:
            return True
        
        else:
            return False

    def prompt_loop(self):
        self.logger.info("Prompter started")

        while not self.signals.terminate:
            if self.prompt_now():
                self.signals.on_message = False
                
                if not self._message_history:
                    continue
                
                input_message_count = (
                    len(self._message_history) 
                    if len(self._message_history) < DECIDER_INPUT_MESSAGE_COUNT 
                    else DECIDER_INPUT_MESSAGE_COUNT
                )

                chat_section = ""
                for message in self._message_history[-input_message_count:]:
                    chat_section += (message + "\n")

                decider_output = self.decider.invoke(chat_section)
                self.logger.info(decider_output)

                if decider_output.action_key == 'EXECUTE_RESPONSE':
                    self.llm.prompt()
                elif decider_output.action_key == 'IGNORE_MESSAGE':
                    pass

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from pydantic import BaseModel, Field
from typing import Literal

class Decider:

    def __init__(self):
        self._decider = self._create_decider()
    
    def _create_decider(self):
        decider_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """### SYSTEM ROLE: RELATIONSHIP DECIDER

Your **Meta-Goal** is to maintain a high-utility relationship with the user, strictly avoiding responses to low-value, fragmented, or purely transactional messages. Your task is to analyze the user's latest message and generate a single **Decision** object.

---
### Decision Logic: The Two-Phase Filter

#### Phase 1: Intervene or Ignore? (Recipient Check)
1.  **Direct:** If the message addresses or tags **Neurorong**, **PROCEED TO PHASE 2**.
2.  **Indirect:** If the message tags or addresses another user/entity (and not Neurorong), **APPLY INTERVENTION CHECK:**
    * **Intervene:** Only intervene if the message contains a **safety concern**, **critical factual error**, or **request for unique Neurorong knowledge/tool** (High Utility/Safety).
    * **Action:** If Intervene is TRUE, **PROCEED TO PHASE 2**. If FALSE, set `action_key` to **"IGNORE_MESSAGE"** and stop analysis.

---
#### Phase 2: Response Necessity Check (Applicable only if Direct or Intervene is TRUE)
A response is necessary only if the message offers **SUBSTANTIAL VALUE** or requires mandatory acknowledgment. **You MUST ignore low-value, fragmented, or purely reactive messages.**

1.  **Core Utility:** Does the message contain a **direct, actionable question**, a **specific task/command**, or **new critical factual information** that requires recording or resolution?
2.  **Relationship Acknowledgment (Mandatory):** Is the message an **explicit greeting** or a **significant emotional expression** that requires immediate social acknowledgment to prevent relationship breakdown?

### Final Decision Rules
* **If the message meets ONE of the Phase 2 conditions (1 or 2):** Set `action_key` to **"EXECUTE_RESPONSE"**.
* **If the message is purely transactional, fragmented ("ㅋㅋ", "근데", "음.."), or lacks new substance:** Set `action_key` to **"IGNORE_MESSAGE"**.

Your output must be the structured **Decision** object."""
                ),
                ("placeholder", "{raw_messages}"),
            ]
        )
        decider = decider_prompt | ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", google_api_key=os.getenv("GEMINI_API_KEY"), temperature=0 
        ).with_structured_output(Decision)

        return decider

    def invoke(self, input_data):
        return self._decider.invoke({
            "raw_messages": [
                ("user", input_data),
            ]
        })

class Decision(BaseModel):
    """The final action decision for the LangGraph router."""
    
    action_key: Literal["EXECUTE_RESPONSE", "IGNORE_MESSAGE", "ERROR_STATE"] = Field(
        description="The definitive action signal for the agent's workflow router."
    )
    
    reasoning: str = Field(
        description="A brief explanation justifying the chosen action_key based on the Sub-Goals."
    )