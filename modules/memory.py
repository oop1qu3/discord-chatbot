from modules.module import Module
from constants import *
from chromadb.config import Settings
from google.genai import types
import chromadb
import requests
import json
import uuid
import asyncio
import copy


class Memory(Module):

    def __init__(self, signals, enabled=True):
        super().__init__(signals, enabled)

        self.API = self.API(self)
        self.prompt_injection.text = ""
        self.prompt_injection.priority = 60

        self.processed_count = 0

        self.chroma_client = chromadb.PersistentClient(path="./memories/chroma.db", settings=Settings(anonymized_telemetry=False))
        self.collection = self.chroma_client.get_or_create_collection(name="neurorong_collection")
        print(f"MEMORY: Loaded {self.collection.count()} memories from database.")
        if self.collection.count() == 0:
            print("MEMORY: No memories found in database. Importing from memoryinit.json")
            self.API.import_json(path="./memories/memoryinit.json")

    def get_prompt_injection(self):
        # Use recent messages and twitch messages to query the database for related memories
        query = ""

        for message in self.signals.recentDiscordMessages:
            query += message + "\n"

        for message in self.signals.history[-MEMORY_QUERY_MESSAGE_COUNT:]:
            if message["role"] == "user" and message["content"] != "":
                query += HOST_NAME + ": " + message["content"] + "\n"
            elif message["role"] == "assistant" and message["content"] != "":
                query += AI_NAME + ": " + message["content"] + "\n"

        memories = self.collection.query(query_texts=query, n_results=MEMORY_RECALL_COUNT)

        # Generate injection for LLM prompt
        self.prompt_injection.text = f"{AI_NAME} knows these things:\n"
        for i in range(len(memories["ids"][0])):
            self.prompt_injection.text += memories['documents'][0][i] + "\n"
        self.prompt_injection.text += "End of knowledge section\n"

        return self.prompt_injection

    async def run(self):
        # Periodically, check if at least 20 new messages have been sent, and if so, generate 3 question-answer pairs
        # to be stored into memory.
        # This is a technique called reflection. You essentially ask the AI what information is important in the recent
        # conversation, and it is converted into a memory so that it can be recalled later.
        while not self.signals.terminate:
            if self.processed_count > len(self.signals.history):
                self.processed_count = 0

            if len(self.signals.history) - self.processed_count >= 20:
                print("MEMORY: Generating new memories")

                # Copy the latest unprocessed messages
                messages = copy.deepcopy(self.signals.history[-(len(self.signals.history) - self.processed_count):])

                for message in messages:
                    if message["role"] == "user" and message["content"] != "":
                        message["content"] = HOST_NAME + ": " + message["content"] + "\n"
                    elif message["role"] == "assistant" and message["content"] != "":
                        message["content"] = AI_NAME + ": " + message["content"] + "\n"

                chat_section = ""
                for message in messages:
                    chat_section += message["content"]

                # 실제 대화 내용을 단일 'user' 메시지로 구성
                conversation_history = [{
                    "role": "user",
                    # chat_section (최근 대화)를 요청 내용으로 전달
                    "parts": [{"text": chat_section}] 
                }]

                # 3개의 질문-답변 쌍을 담을 JSON 스키마 정의
                memory_schema = types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "memories": types.Schema(
                            type=types.Type.ARRAY,
                            items=types.Schema(
                                type=types.Type.OBJECT,
                                properties={
                                    "question": types.Schema(type=types.Type.STRING),
                                    "answer": types.Schema(type=types.Type.STRING),
                                },
                                required=["question", "answer"],
                            ),
                        )
                    },
                    required=["memories"]
                )

                try:
                    # 2. 비동기 호출: requests.post 대신 AsyncClient 사용
                    response = await self.global_model.models.generate_content(
                        model='gemini-2.0-flash',  # 적절한 Gemini 모델 선택
                        contents=conversation_history,
                        config={
                            "system_instruction": MEMORY_PROMPT, # MEMORY_PROMPT는 이제 모델 역할 정의에 집중
                            "max_output_tokens": 500, # JSON 출력에 맞춰 토큰 증가
                            "response_mime_type": "application/json", # 🚨 JSON 출력 강제
                            "response_schema": memory_schema        # 🚨 스키마 정의
                        }
                    )
                    
                    # 3. 응답에서 내용 추출
                    raw_memories = response.text
                    print(f"MEMORY: Raw memories generated: {raw_memories[:50]}...")
                    
                    try:
                        # 1. JSON 문자열 파싱
                        # response.text는 JSON 모드 설정 덕분에 유효한 JSON 문자열일 것입니다.
                        raw_memories_json_str = response.text
                        
                        # JSON 문자열을 파이썬 딕셔너리로 변환
                        memory_data = json.loads(raw_memories_json_str)

                        # 2. 메모리 추출 및 데이터베이스에 upsert
                        new_memories_to_upsert = []
                        
                        # JSON 스키마의 'memories' 배열을 반복하며 Q&A 쌍을 추출
                        for item in memory_data.get('memories', []):
                            question = item.get('question', '').strip()
                            answer = item.get('answer', '').strip()
                            
                            # Q&A 쌍을 하나의 문자열로 결합 (컬렉션에 저장될 Document)
                            if question and answer:
                                # 질문과 답변을 명확하게 구분하는 포맷을 사용하여 저장
                                full_memory = f"Q: {question}\nA: {answer}" 
                                new_memories_to_upsert.append(full_memory)

                        # 3. 데이터베이스에 일괄 저장 (Upsert)
                        if new_memories_to_upsert:
                            ids = [str(uuid.uuid4()) for _ in new_memories_to_upsert]
                            
                            # upsert는 비동기 작업일 수 있으므로 self.collection이 비동기를 지원하는지 확인해야 함
                            # ChromaDB Python 클라이언트의 upsert는 일반적으로 동기 함수이므로, 그대로 사용.
                            self.collection.upsert(
                                ids=ids,
                                documents=new_memories_to_upsert,
                                metadatas=[{"type": "short-term"}] * len(ids)
                            )
                            print(f"MEMORY: {len(new_memories_to_upsert)}개의 새로운 메모리가 데이터베이스에 추가되었습니다.")

                        # 4. 처리된 메시지 카운트 업데이트
                        self.processed_count = len(self.signals.history) 

                    except json.JSONDecodeError as e:
                        print(f"MEMORY: JSON 파싱 오류 발생. 원본 텍스트: {raw_memories_json_str[:100]}...")
                    except Exception as e:
                        print(f"MEMORY: 메모리 저장 중 일반 오류 발생: {e}")
                    
                    # 처리된 메시지 카운트 업데이트
                    self.processed_count = len(self.signals.history) 

                except Exception as e:
                    print(f"MEMORY: Gemini API 호출 중 오류 발생: {e}")
                    await asyncio.sleep(5) # 오류 발생 시 잠시 대기

            await asyncio.sleep(5)

    class API:
        def __init__(self, outer):
            self.outer = outer

        def create_memory(self, data):
            id = str(uuid.uuid4())
            self.outer.collection.upsert(id, documents=data, metadatas={"type": "short-term"})

        def delete_memory(self, id):
            self.outer.collection.delete(id)

        def wipe(self):
            self.outer.chroma_client.reset()
            self.outer.chroma_client.create_collection(name="neuro_collection")

        def clear_short_term(self):
            short_term_memories = self.outer.collection.get(where={"type": "short-term"})
            for id in short_term_memories["ids"]:
                self.outer.collection.delete(id)

        def import_json(self, path="./memories/memories.json"):
            with open(path, "r") as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    print("Error decoding JSON file")
                    return

            for memory in data["memories"]:
                self.outer.collection.upsert(memory["id"], documents=memory["document"], metadatas=memory["metadata"])

        def export_json(self, path="./memories/memories.json"):
            memories = self.outer.collection.get()

            data = {"memories": []}
            for i in range(len(memories["ids"])):
                data["memories"].append({"id": memories["ids"][i],
                                         "document": memories["documents"][i],
                                        "metadata": memories["metadatas"][i]})

            with open(path, "w") as file:
                json.dump(data, file)

        def get_memories(self, query=""):
            data = []

            if query == "":
                memories = self.outer.collection.get()
                for i in range(len(memories["ids"])):
                    data.append({"id": memories["ids"][i],
                                 "document": memories["documents"][i],
                                 "metadata": memories["metadatas"][i]})
            else:
                memories = self.outer.collection.query(query_texts=query, n_results=30)
                for i in range(len(memories["ids"][0])):
                    data.append({"id": memories["ids"][0][i],
                                 "document": memories["documents"][0][i],
                                 "metadata": memories["metadatas"][0][i],
                                 "distance": memories["distances"][0][i]})

                # Sort memories by distance
                data = sorted(data, key=lambda x: x["distance"])
            return data