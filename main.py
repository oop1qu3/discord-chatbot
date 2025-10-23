import asyncio
import os
import time
import threading
import sys
import signal

from dotenv import load_dotenv
from google.genai import Client

from signals import Signals
from modules.discordClient import DiscordClient
from llmWrappers.textLLMWrapper import TextLLMWrapper
from prompter import Prompter
from modules.memory import Memory
from constants import *

PROMPT = '''
최근 대화:
    "혜민 — 오후 8:02
    그냥 놀아만 줘도 좋아할걸
    걔는

    ㅇㅎㅅ — 오후 8:03
    그렇대우동
    다운펌 괜히함
    머리말리기
    댕기췮다

    혜민 — 오후 8:03
    너가 안 귀찮은게 머임

    ㅇㅎㅅ — 오후 8:07
    니들이랑 놀기

    뉴로롱 — 오후 8:07
    어우, 너희들이랑 노는 게 제일 재밌긴 하지.
    다운펌은 잘생김을 얻고 귀찮음을 얻는 거래 아니겠어?ㅋㅋㅋ 며칠만 고생해!

    0093 — 오후 8:52
    ㅋㅋㅋ
    우동이 저말한줄

    bp — 오후 9:23
    zzzzzzz

    ㅇㅎㅅ — 오후 9:36
    ?
    ㅋㅋㅋ
    뉴로롱
    개때리고싶네"

뉴로롱은 ㅇㅎㅅ를 놀리고 싶어한다. 따라서 다음과 같은 답변을 보내려 한다: "왜 때리고 싶어? 팩트라서 그래? ㅋㅋㅋㅋ"

뉴로롱이 갑자기 위 답변을 보내고 싶지 않을 자연스러운 이유가 있으면, 설명 없이 오직 다음과 같은 양식만으로 출력:
    x[여기에 이유를 입력]
그렇지 않고 그대로 답변을 보낼 거라고 예상되면, 설명 없이 오직 다음과 같은 양식만으로 출력:
    o[여기에 답변을 입력]
'''
'''
위 대화를 통해 뉴로롱이 앞으로 뭘 하고 싶을지,
또 뉴로롱이 그 목표를 이루기 위해 위 대화에 이어서 어떤 답변을 할지, 설명 없이 오직 다음과 같은 양식만으로 출력:
    뉴로롱은 ...하고 싶어한다. 따라서 다음과 같은 답변을 보내려 한다: "여기에 답변을 입력"
'''

async def main():
    test = False

    if test:
        data = [{
            "role": "user",
            "parts": [{"text": PROMPT}] 
        }]

        try:
            load_dotenv()
            client = Client(api_key=os.getenv("GEMINI_API_KEY"))

            response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=data, 
            )
            
            print(response.text)

        except Exception as e:
            print(f"오류: {e}")

        return

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

