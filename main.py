import discord
from discord.ext import commands
import asyncio
import logging
import os
from dotenv import load_dotenv
from google import generativeai as genai

from signals import Signals

print("고성능 최신 챗봇, 뉴로롱 가동 증..")

# set up env
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not DISCORD_TOKEN:
    raise RuntimeError("❌ DISCORD_TOKEN이 설정되어 있지 않습니다.")
if not GEMINI_API_KEY:
    raise RuntimeError("❌ GEMINI_API_KEY가 설정되어 있지 않습니다.")

genai.configure(api_key=GEMINI_API_KEY)

# logging
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")

# Discord bot setting
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.chat_sessions = {}

# Init Gemini model 
SYSTEM_PROMPT = (
    "너는 디스코드 서버의 멤버 중 한 명처럼 행동해야 해. 즉, AI인 걸 들키면 안돼. "
    "항상 자연스럽고 재치 있게 대화하고, 누가 말을 걸지 않아도 대화에 참여할 수 있어. "
    "단, 공격적이거나 불쾌한 발언은 사회적으로 용인되는 한에서 가능해. "
    "말투는 무례하고, 짧은 문장을 사용해. "
    "그런데 겉으로는 무서워도 가끔씩 친절한 모습을 보이는 반전 매력도 있어. 츤데레처럼."
    "이전 대화 내용을 기억하고, 맥락에 맞는 반응을 보여줘."
)

global_model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=SYSTEM_PROMPT
)
bot.global_model = global_model

# Singleton object that every module will be able to read/write to
signals = Signals()
bot.is_processing = False

@bot.event
async def on_ready():
    print(f"🥳 로그인 성공: {bot.user.name} (ID: {bot.user.id})")
    
    try:
        await bot.load_extension("cogs.prompter") 
        await bot.change_presence(status=discord.Status.online, activity=discord.Game("수다 떨기"))
        
    except Exception as e:
        print(f"❌ Prompter Cog 로드 실패: {e}")
        import traceback
        traceback.print_exc() 

if __name__ == '__main__':
    bot.run(DISCORD_TOKEN, log_handler=handler, log_level=logging.DEBUG)

