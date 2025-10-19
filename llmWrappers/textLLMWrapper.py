import os
from dotenv import load_dotenv
from google import generativeai as genai

class TextLLMWrapper:
    def __init__(self, discordBot, signals) -> None:
        self.discordBot = discordBot
        self.signals = signals

        # set up env
        load_dotenv()
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

        # Init Gemini model 
        SYSTEM_PROMPT = (
            "너는 디스코드 서버의 멤버 중 한 명처럼 행동해야 해. 즉, AI인 걸 들키면 안돼. "
            "항상 자연스럽고 재치 있게 대화하고, 누가 말을 걸지 않아도 대화에 참여할 수 있어. "
            "단, 공격적이거나 불쾌한 발언은 사회적으로 용인되는 한에서 가능해. "
            "말투는 무례하고, 짧은 문장을 사용해. "
            "그런데 겉으로는 무서워도 가끔씩 친절한 모습을 보이는 반전 매력도 있어. 츤데레처럼."
            "이전 대화 내용을 기억하고, 맥락에 맞는 반응을 보여줘."
        )

        self.global_model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=SYSTEM_PROMPT
        )
    '''
    def prepare_payload(self):
        return {
            "mode": "instruct",
            "stream": True,
            "max_tokens": 200,
            "skip_special_tokens": False,  # Necessary for Llama 3
            "custom_token_bans": BANNED_TOKENS,
            "stop": STOP_STRINGS,
            "messages": [{
                "role": "user",
                "content": self.generate_prompt()
            }]
        }
    '''
    async def prompt(self):
        message = await self.signals.message_queue_in.get()

        if message is None:
            return
        
        if message.content:

            self.signals.is_processing = True 
            channel_id = message.channel.id

            try:
                if channel_id not in self.signals.chat_sessions:
                    print(f"[DEBUG] 세션 없음 → 생성 시도 중 (채널 {channel_id})")
                    self.signals.chat_sessions[channel_id] = self.global_model.start_chat(history=[])
                    print(f"🆕 새로운 채팅 세션 생성: {channel_id}")

                chat = self.signals.chat_sessions[channel_id]

                formatted_message = f"{message.author.display_name}: {message.content}"

                # Gemini에 메시지 전송
                response = chat.send_message(formatted_message)
                print(f"> 보낼 메시지: {response.text}")

                if response.text:
                    self.signals.message_queue_out.put_nowait((channel_id, response.text))

            except Exception as e:
                print(f"Gemini 응답 오류: {e}")
                
            finally:
                # 응답 완료 후 '생각 중' 상태 해제
                self.signals.is_processing = False
                self.signals.message_queue_in.task_done()