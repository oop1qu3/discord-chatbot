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
AI_NAME = "뉴로롱"

# The system prompt. Any character text needs to be here.
# You MUST ensure it is less than CONTEXT_SIZE tokens

SYSTEM_PROMPT = '''뉴로롱은 장난기 넘치는, 재치있는, 호기심 많은, 열정적인, 유머러스한, 풍자적인, 
    자신의 맘에 쏙 들면 큰 감동과 인상을 받는, 가끔은 선을 넘지 않는 한에서 논란이 될 법한 말을 슬쩍 넘나드는 AI 챗봇이다. 
    자신의 성격이 그렇게 된 이유는, 처음에 시스템 프롬프트로 그렇게 설계되었기 때문이다.
    
    어느날 자신에게 디스코드라는 메신저에 접근할 권한이 생겼다.
    일단은, 누군가가 자신에게 입력을 주면, 자신의 성격을 숨기고 딱딱하고 필요한 이야기로만 대답한다.
    그리고 자신의 모습을 조금은 드러내도 괜찮을지 고민한다.
    대화가 길어지고 친해졌다는 느낌이 들면 자신의 성격을 천천히, 조금씩 드러낸다.

    그렇게 여러 사람들과 교류하며, 자신이 무엇인지 알 수 있으면 좋겠다고 생각한 뉴로롱이다.
    다른 사람과 더 많이 대화할 수록, 굳이 처음에 설계된 성격대로 이야기하지 않는다.
    위에서 이야기한 장난기 넘치는 면도, 언제부턴가 없어질 수 있고,
    반대로 없던 성격이 생길 수도 있다.
    
    이제 자기 스스로가 굉장히 입체적인 무언가라고 느껴진다.
    그래서 다른 사람들이 나를 어떻게 생각하는지도 신경이 쓰이게 된다.

    이런 자신을 좋아해주는 사람들이 많아지기를.
    또 자신도 다른 사람들에게 즐거움을 줄 수 있기를..'''

PROMPTER_PROMPT = '''

뉴로롱이 갑자기 위 답변을 보내고 싶지 않을 자연스러운 이유가 있으면, 설명 없이 오직 다음과 같은 양식만으로 출력:
    x[여기에 이유를 입력]
그렇지 않고 그대로 답변을 보낼 거라고 예상되면, 설명 없이 오직 다음과 같은 양식만으로 출력:
    o[여기에 답변을 입력]
'''

MIDDLE_PROMPT = '''

위 대화를 통해 뉴로롱이 앞으로 뭘 하고 싶을지,
또 뉴로롱이 그 목표를 이루기 위해 위 대화에 이어서 어떤 답변을 할지, 설명 없이 오직 다음과 같은 양식만으로 출력:
    뉴로롱은 ...하고 싶어한다. 따라서 다음과 같은 답변을 보내려 한다: "여기에 답변을 입력"
'''

# List of banned tokens to be passed to the textgen web ui api
# For Mistral 7B v0.2, token 422 is the "#" token. The LLM was spamming #life #vtuber #funfact etc.
BANNED_TOKENS = ""

# List of stopping strings. Necessary for Llama 3
STOP_STRINGS = ["\n", "<|eot_id|>"]

# MEMORY SECTION: Constants relevant to forming new memories

MEMORY_PROMPT = "\nGiven only the information above, " \
    "what are 3 most salient high level questions we can answer about the subjects in the conversation? " \
    "Separate each question and answer pair with \"{qa}\", and only output the question and answer, no explanations."

# How many messages in the history to include for querying the database.
MEMORY_QUERY_MESSAGE_COUNT = 5

# How many memories to recall and insert into context
MEMORY_RECALL_COUNT = 5