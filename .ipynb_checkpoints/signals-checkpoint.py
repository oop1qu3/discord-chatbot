import asyncio

class Signals:
    def __init__(self):
        self.last_message_time = 0.0

        # This flag indicates to all threads that they should immediately terminate
        self._terminate = False

        self._recentDiscordMessages = []
        self._history = []

        # This flag indicates to discord bot that it received message, exectuting prompt
        self.on_message = False
        self.AI_thinking = False
        self.send_now = False
        self.online = False

        self.AI_message = ""
        self.recentChannel = None
        self.logger = None
        self.client = None
        self.API = None

    @property
    def recentDiscordMessages(self):
        return self._recentDiscordMessages

    @recentDiscordMessages.setter
    def recentDiscordMessages(self, value):
        self._recentDiscordMessages = value

    @property
    def history(self):
        return self._history

    @history.setter
    def history(self, value):
        self._history = value

    @property
    def terminate(self):
        return self._terminate

    @terminate.setter
    def terminate(self, value):
        self._terminate = value