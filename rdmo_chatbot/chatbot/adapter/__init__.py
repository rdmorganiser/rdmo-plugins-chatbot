class BaseAdapter:
    def __init__(self, cl, config):
        raise NotImplementedError

    async def on_message(self, message):
        raise NotImplementedError
