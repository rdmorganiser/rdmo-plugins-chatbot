class BaseAdapter:
    def __init__(self, cl, settings):
        raise NotImplementedError

    async def on_message(self, message):
        raise NotImplementedError
