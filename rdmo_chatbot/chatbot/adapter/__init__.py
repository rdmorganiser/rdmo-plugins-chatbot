class BaseAdapter:
    def __init__(self, cl, config):
        self.cl = cl
        self.config = config

    async def on_chat_start(self):
        pass

    async def on_chat_end(self):
        pass

    async def on_chat_resume(self, thread):
        pass

    async def on_message(self, message):
        raise NotImplementedError
