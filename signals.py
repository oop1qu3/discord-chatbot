import asyncio

class Signals:
    def __init__(self):
        # This flag indicates to all threads that they should immediately terminate
        self._terminate = False

        # This flag indicates to discord bot that it received message, exectuting prompt
        self.on_message = False
        self.AI_thinking = False
        self.send_now = False
        self.online = False

        self.fragmented_response = []
        self.API = None

    @property
    def terminate(self):
        return self._terminate

    @terminate.setter
    def terminate(self, value):
        self._terminate = value