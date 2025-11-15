import logging
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
import datetime


class Memory(Module):

    def __init__(self, signals, enabled=True):
        super().__init__(signals, enabled)

        self.API = self.API(self)
        self.processed_count = 0

        self.logger = logging.getLogger("memory")
        self._message_history = []


        self.chroma_client = chromadb.PersistentClient(path="./memories/chroma.db", settings=Settings(anonymized_telemetry=False))
        self.collection = self.chroma_client.get_or_create_collection(name="neurorong_collection")
        self.logger.info(f"MEMORY: Loaded {self.collection.count()} memories from database.")

        if self.collection.count() == 0:
            self.logger.info("MEMORY: No memories found in database. Importing from memoryinit.json")
            self.API.import_json(path="./memories/memoryinit.json")

    def setMessageHistory(self, message_history):
        self._message_history = message_history

    async def run(self):
        pass

    class API: #FIXME
        def __init__(self, outer):
            self.outer = outer

        def create_memory(self, data):
            id = str(uuid.uuid4())
            self.outer.collection.upsert(id, documents=data, metadatas={"type": "short-term"})

        def delete_memory(self, id):
            self.outer.collection.delete(id)

        def wipe(self):
            self.outer.chroma_client.reset()
            self.outer.chroma_client.create_collection(name="neurorong_collection")

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