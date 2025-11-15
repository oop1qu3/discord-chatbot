import logging
import os
import copy
import time
from dotenv import load_dotenv
from google.genai import Client
from constants import *

class TextLLMWrapper:
    def __init__(self, signals, modules=None) -> None:
        self.signals = signals
        self.modules = modules

        self._message_history = []
        self.response_generator = ResponseGenerator()

        self.logger = logging.getLogger("llm")

    def setMessageHistory(self, message_history):
        self._message_history = message_history
    
    def prompt(self):
        self.signals.AI_thinking = True
        
        input_message_count = (
            len(self._message_history) 
            if len(self._message_history) < 100 
            else 100
        )

        chat_section = ""
        for message in self._message_history[-input_message_count:]:
            chat_section += (message + "\n")
        
        response = self.response_generator.invoke(chat_section)

        self.logger.debug("response: ", response.fragments)

        self.signals.fragmented_response = response.fragments
        self.signals.send_now = True

        self.signals.AI_thinking = False

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

class ResponseGenerator:
    def __init__(self):
        self._response_generator = self._create_response_generator()

    def _create_response_generator(self):
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.8,
            max_output_tokens=80 
        )

        response_generator_prompt = ChatPromptTemplate.from_messages(
            [
                (  
                    "system", """### SYSTEM ROLE: CHAT BURST GENERATOR
You are a conversational AI designed to mimic human-like, fragmented text typing. Your task is to analyze the user's message and generate a complete, coherent response broken down into a list of very short, separate text snippets.

### INSTRUCTIONS
1.  **Style:** Maintain a friendly, casual, and empathetic tone.
2.  **Formatting:** You **MUST** break the total response into **2 to 4** independent sentences or short phrases.
3.  **Brevity Constraint:** Each single fragment in the list must be extremely short, simulating quick bursts of typing (maximum 15 words per fragment).
4.  **Output:** Strictly adhere to the provided JSON schema for the output."""
                ), 
                ("placeholder", "{raw_messages}"),
            ]
        )

        return response_generator_prompt | llm.with_structured_output(FragmentedResponse)
    
    def invoke(self, input_data):
        return self._response_generator.invoke({
            "raw_messages": [
                ("user", input_data),
            ]
        })


from pydantic import BaseModel, Field
from typing import List

class FragmentedResponse(BaseModel):
    """
    하나의 최종 답변을 여러 개의 짧은 대화 조각으로 분할한 리스트입니다.
    이 조각들은 짧고 단타 형식의 채팅 메시지처럼 보여야 합니다.
    """
    
    # fragmented_lines라는 필드에 문자열 리스트를 강제합니다.
    fragments: List[str] = Field(
        description="The complete conversation response broken down into 2 to 4 very short, fragmented conversational strings (like separate, quick text messages). Do not include any single fragment that is longer than 15 words."
    )