# This file holds various constants used in the program
# Variables marked with #UNIQUE# will be unique to your setup and NEED to be changed or the program will not work correctly.

# Discord messages above this length will be ignored
DISCORD_MAX_MESSAGE_LENGTH = 300

# Twitch channel for bot to join
#UNIQUE#
DISCORD_CHANNEL = "lunasparkai"

# Context size (maximum number of tokens in the prompt) Will target upto 90% usage of this limit
CONTEXT_SIZE = 8192

# This is your name
#UNIQUE#
HOST_NAME = "단아히"

# This is the AI's name
AI_NAME = "_뉴로롱"

# The system prompt. Any character text needs to be here.
# You MUST ensure it is less than CONTEXT_SIZE tokens

SYSTEM_PROMPT = ''

MIDDLE_PROMPT = '''위 대화를 통해 뉴로롱이 앞으로 뭘 하고 싶을지,
또 뉴로롱이 그 목표를 이루기 위해 위 대화에 이어서 어떤 답변을 할지, 설명 없이 오직 다음과 같은 양식만으로 출력:
    뉴로롱은 ...하고 싶어한다. 따라서 다음과 같은 답변을 보내려 한다: "답변"'''

PROMPTER_PROMPT = '''뉴로롱이 갑자기 위 답변을 보내고 싶지 않을 자연스러운 이유가 있으면, 설명 없이 오직 다음과 같은 양식만으로 출력:
    x[이유]
그렇지 않고 그대로 답변을 보낼 거라고 예상되면, 설명 없이 오직 다음과 같은 양식만으로 출력:
    o[답변]'''

# List of banned tokens to be passed to the textgen web ui api
# For Mistral 7B v0.2, token 422 is the "#" token. The LLM was spamming #life #vtuber #funfact etc.
BANNED_TOKENS = ""

# List of stopping strings. Necessary for Llama 3
STOP_STRINGS = ["\n", "<|eot_id|>"]

# MEMORY SECTION: Constants relevant to forming new memories

MEMORY_PROMPT = '''위 정보가 주어졌을 때, 대화 속 주제에 대하여 우리가 대답할 수 있는 가장 질 좋은 질문 3가지는 무엇인가?
각각의 질문-답 쌍을 \"{qa}\"로 나눠, 설명 없이 오직 질문-답을 출력하라'''

# How many messages in the history to include for querying the database.
MEMORY_QUERY_MESSAGE_COUNT = 5

# How many memories to recall and insert into context
MEMORY_RECALL_COUNT = 5

# How many messages in the history to include for executing the decider.
DECIDER_INPUT_MESSAGE_COUNT = 20

MIN_SLEEP_TIME = 0.5  # 최소 0.5초 대기
CHAR_DELAY_FACTOR = 0.3 # 글자당 0.3초 추가
MAX_SLEEP_TIME = 9.5   # 최대 9.5초 대기