import json

from .base import BaseStore
from . import config

import redis

class RedisStore(BaseStore):
    def __init__(self):
        self.redis_client = redis.Redis(**config.STORE_CONNECTION)

    def has_history(self, user_identifier, project_id):
        key = f"history:{user_identifier}:{project_id}"
        return self.redis_client.exists(key)

    def get_history(self, user_identifier, project_id):
        key = f"history:{user_identifier}:{project_id}"
        history_json = self.redis_client.get(key)
        breakpoint()
        return dicts_to_messages(json.loads(history_json)) if history_json else []

    def set_history(self, user_identifier, project_id, history):
        key = f"history:{user_identifier}:{project_id}"
        self.redis_client.set(key, json.dumps(messages_to_dicts(history)))
        if hasattr(config, "STORE_TTL"):
            self.redis_client.expire(key, config.STORE_TTL)

    def reset_history(self, user_identifier, project_id):
        key = f"history:{user_identifier}:{project_id}"
        self.redis_client.delete(key)
