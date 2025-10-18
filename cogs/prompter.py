import discord
from discord.ext import commands
import asyncio
import random

class Prompter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 봇의 is_processing 상태를 여기서 관리할 수도 있습니다.
        # self.bot.is_processing = False 
        print("✅ Prompter Cog 로드 완료.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # test
        print(f"📩 받은 메시지: {message.content}")

        # 자기 자신 무시
        if message.author.bot:
            return
        
        # 1) 명령어 처리 (가장 먼저 실행)
        if message.content.startswith("!"):
            return

        # 2) 봇이 이미 응답 중일 때 차단
        if self.bot.is_processing:
            return
        
        # 3) 필터링: 메시지 길이 짧으면 무시
        if len(message.content) < 5:
            if random.random() < 0.75: 
                return

        # 4) 필터링: 응답 확률 (60% 확률로 응답)
        if random.random() < 0.50:
            return

        # --- 필터 통과: 응답 준비 시작 ---
        print("필터 통과")
        self.bot.is_processing = True 
        
        channel_id = message.channel.id

        try:
            if channel_id not in self.bot.chat_sessions:
                print(f"[DEBUG] 세션 없음 → 생성 시도 중 (채널 {channel_id})")
                self.bot.chat_sessions[channel_id] = self.bot.global_model.start_chat(history=[])
                print(f"🆕 새로운 채팅 세션 생성: {channel_id}")

            chat = self.bot.chat_sessions[channel_id]

            await asyncio.sleep(random.uniform(2, 5))

            formatted_message = f"{message.author.display_name}: {message.content}"

            # Gemini에 메시지 전송
            response = chat.send_message(formatted_message)

            # Gemini 응답 전송
            await message.channel.send(response.text)

        except Exception as e:
            print(f"❌ Gemini 응답 오류: {e}")
            await message.channel.send("앗, 잠시 생각 중이에요... 🤔")

        finally:
            # 7) 응답 완료 후 '생각 중' 상태 해제
            self.bot.is_processing = False

# 봇이 Cog를 로드할 수 있도록 setup 함수를 정의
async def setup(bot):
    await bot.add_cog(Prompter(bot))