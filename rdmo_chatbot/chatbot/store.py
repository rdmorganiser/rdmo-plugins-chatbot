import json

from utils import dicts_to_messages, get_config, messages_to_dicts

config = get_config()


class BaseStore:

    def has_history(self, user_identifier, project_id):
        raise NotImplementedError

    def get_history(self, user_identifier, project_id):
        raise NotImplementedError

    def set_history(self, user_identifier, project_id, history):
        raise NotImplementedError

    def reset_history(self, user_identifier, project_id):
        raise NotImplementedError


class LocMemStore(BaseStore):

    _instance = None
    _store = {}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.data = {}
        return cls._instance

    def has_history(self, user_identifier, project_id):
        return self._store.get(user_identifier, {}).get(project_id) is not None

    def get_history(self, user_identifier, project_id):
        return self._store.get(user_identifier, {}).get(project_id , [])

    def set_history(self, user_identifier, project_id, history):
        if user_identifier not in self._store:
            self._store[user_identifier] = {}

        self._store[user_identifier][project_id] = history

    def reset_history(self, user_identifier, project_id):
        if self.has_history(user_identifier, project_id):
            del self._store[user_identifier][project_id]


class RedisStore(BaseStore):
    def __init__(self):
        import redis
        self.redis_client = redis.Redis(**config.STORE_CONNECTION)

    def has_history(self, user_identifier, project_id):
        key = f"history:{user_identifier}:{project_id}"
        return self.redis_client.exists(key)

    def get_history(self, user_identifier, project_id):
        key = f"history:{user_identifier}:{project_id}"
        history_json = self.redis_client.get(key)
        return dicts_to_messages(json.loads(history_json)) if history_json else []

    def set_history(self, user_identifier, project_id, history):
        key = f"history:{user_identifier}:{project_id}"
        self.redis_client.set(key, json.dumps(messages_to_dicts(history)))
        if hasattr(config, "STORE_TTL"):
            self.redis_client.expire(key, config.STORE_TTL)

    def reset_history(self, user_identifier, project_id):
        key = f"history:{user_identifier}:{project_id}"
        self.redis_client.delete(key)


class Sqlite3Store(BaseStore):

    def __init__(self):
        import sqlite3
        self.connection = sqlite3.connect(config.STORE_CONNECTION)
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_identifier TEXT,
                project_id INTEGER,
                messages JSON,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_identifier, project_id)
            );
        """)
        self.connection.commit()

    def has_history(self, user_identifier, project_id):
        self.cursor.execute("""
            SELECT count(*) FROM history WHERE user_identifier = ? AND project_id = ?;
        """, (user_identifier, project_id))
        result = self.cursor.fetchone()
        return result[0] > 0 if result else False

    def get_history(self, user_identifier, project_id):
        self.cursor.execute("""
            SELECT messages FROM history WHERE user_identifier = ? AND project_id = ?;
        """, (user_identifier, project_id))
        result = self.cursor.fetchone()
        return dicts_to_messages(result[0]) if result else []

    def set_history(self, user_identifier, project_id, messages):
        self.cursor.execute("""
            INSERT INTO history (user_identifier, project_id, messages) VALUES (?, ?, ?)
            ON CONFLICT (user_identifier, project_id) DO UPDATE SET
                messages = EXCLUDED.messages,
                updated = CURRENT_TIMESTAMP;
        """, (user_identifier, project_id, json.dumps(messages_to_dicts(messages))))
        self.connection.commit()

    def reset_history(self, user_identifier, project_id):
        self.cursor.execute("""
            DELETE FROM history WHERE user_identifier = ? AND project_id = ?;
        """, (user_identifier, project_id))
        self.connection.commit()


class PostgresStore(BaseStore):
    def __init__(self):
        import psycopg
        self.connection = psycopg.connect(**config.STORE_CONNECTION)
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                user_identifier VARCHAR(150),
                project_id INT,
                messages JSONB,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (user_identifier, project_id)
            );
        """)
        self.connection.commit()

    def has_history(self, user_identifier, project_id):
        self.cursor.execute("""
            SELECT count(*) FROM history WHERE user_identifier = %s AND project_id = %s;
        """, (user_identifier, project_id))
        result = self.cursor.fetchone()
        return result[0] > 0 if result else False

    def get_history(self, user_identifier, project_id):
        self.cursor.execute("""
            SELECT messages FROM history WHERE user_identifier = %s AND project_id = %s;
        """, (user_identifier, project_id))
        result = self.cursor.fetchone()
        return dicts_to_messages(result[0]) if result else []

    def set_history(self, user_identifier, project_id, messages):
        self.cursor.execute("""
            INSERT INTO history (user_identifier, project_id, messages, created) VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (user_identifier, project_id) DO UPDATE SET
                messages = EXCLUDED.messages,
                updated = CURRENT_TIMESTAMP;
        """, (user_identifier, project_id, json.dumps(messages_to_dicts(messages))))
        self.connection.commit()

    def reset_history(self, user_identifier, project_id):
        self.cursor.execute("""
            DELETE FROM history WHERE user_identifier = %s AND project_id = %s;
        """, (user_identifier, project_id))
        self.connection.commit()


class MysqlStore(BaseStore):

    def __init__(self):
        import MySQLdb
        self.connection = MySQLdb.connect(**config.STORE_CONNECTION)
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_identifier VARCHAR(150),
                project_id INT,
                messages JSON,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_user_project (user_identifier, project_id)
            );
        """)
        self.connection.commit()

    def has_history(self, user_identifier, project_id):
        self.cursor.execute("""
            SELECT count(*) FROM history WHERE user_identifier = %s AND project_id = %s;
        """, (user_identifier, project_id)
        )
        result = self.cursor.fetchone()
        return result[0] > 0 if result else False

    def get_history(self, user_identifier, project_id):
        self.cursor.execute("""
            SELECT messages FROM history WHERE user_identifier = %s AND project_id = %s;
        """, (user_identifier, project_id)
        )
        result = self.cursor.fetchone()
        return dicts_to_messages(json.loads(result[0])) if result else []

    def set_history(self, user_identifier, project_id, messages):
        self.cursor.execute("""
            INSERT INTO history (user_identifier, project_id, messages, created) VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON DUPLICATE KEY UPDATE
                messages = VALUES(messages),
                updated = CURRENT_TIMESTAMP;
        """, (user_identifier, project_id, json.dumps(messages_to_dicts(messages))))
        self.connection.commit()

    def reset_history(self, user_identifier, project_id):
        self.cursor.execute("""
            DELETE FROM history WHERE user_identifier = %s AND project_id = %s;
        """, [user_identifier, project_id]
        )
        self.connection.commit()
