import asyncio

class Signals:
    def __init__(self):
        self.chat_sessions = {}
        self.is_processing = False
        self.last_message_time = 0.0

        # This flag indicates to all threads that they should immediately terminate
        self._terminate = False

        self.message_queue_in = asyncio.Queue()
        self.message_queue_out = asyncio.Queue()

    @property
    def terminate(self):
        return self._terminate

    @terminate.setter
    def terminate(self, value):
        self._terminate = value