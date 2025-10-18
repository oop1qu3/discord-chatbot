import discord
from discord.ext import commands
import random
import asyncio
import logging
import os
from dotenv import load_dotenv
from google import generativeai as genai  # 최신 SDK 기준

# --- 1. 환경 변수 및 설정 ---
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not DISCORD_TOKEN:
    raise RuntimeError("❌ DISCORD_TOKEN이 설정되어 있지 않습니다.")
if not GEMINI_API_KEY:
    raise RuntimeError("❌ GEMINI_API_KEY가 설정되어 있지 않습니다.")

genai.configure(api_key=GEMINI_API_KEY)

# --- 2. 로깅 설정 ---
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")

# --- 3. Discord 봇 기본 설정 ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- 4. Gemini 모델 초기화 ---
SYSTEM_PROMPT = (
    "너는 디스코드 서버의 멤버 중 한 명처럼 행동해야 해. 즉, AI인 걸 들키면 안돼. "
    "항상 자연스럽고 재치 있게 대화하고, 누가 말을 걸지 않아도 대화에 참여할 수 있어. "
    "단, 공격적이거나 불쾌한 발언은 절대 하지 않아. "
    "말투는 편안하고, 짧은 문장을 사용해. "
    "이전 대화 내용을 기억하고, 맥락에 맞는 반응을 보여줘."
)

global_model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=SYSTEM_PROMPT
)

# 채널별 세션 저장소
chat_sessions = {}

# --- 5. 봇 이벤트 ---
@bot.event
async def on_ready():
    print(f"로그인 성공: {bot.user.name}")
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("수다 떨기"))

# --- 6. 메시지 이벤트 ---
@bot.event
async def on_message(message: discord.Message):
    # test
    print(f"📩 받은 메시지: {message.content}")

    # 자기 자신 무시
    if message.author.bot:
        return

    # 명령어 처리 (!로 시작하는 경우는 기본 명령어 처리)
    await bot.process_commands(message)
    if message.content.startswith("!"):
        return

    # 1) 메시지 길이 짧으면 무시
    if len(message.content) < 15:
        return

    # 2) 20% 확률로만 응답
    #if random.random() < 0.80:
    #   return

    # 3) 채널별 세션 로드 또는 생성
    channel_id = message.channel.id

    if channel_id not in chat_sessions:
        print(f"[DEBUG] 세션 없음 → 생성 시도 중 (채널 {channel_id})")
        chat_sessions[channel_id] = global_model.start_chat(history=[])
        print(f"🆕 새로운 채팅 세션 생성: {channel_id}")

    chat = chat_sessions[channel_id]

    # 4) 자연스러운 지연 (2~5초)
    await asyncio.sleep(random.uniform(2, 5))

    try:
        formatted_message = f"{message.author.display_name}: {message.content}"

        # Gemini에 메시지 전송
        response = chat.send_message(formatted_message)

        # Gemini 응답 전송
        await message.channel.send(response.text)

    except Exception as e:
        print(f"❌ Gemini 응답 오류: {e}")
        await message.channel.send("앗, 잠시 생각 중이에요... 🤔")


# --- 7. 봇 실행 ---
bot.run(DISCORD_TOKEN, log_handler=handler, log_level=logging.DEBUG)

