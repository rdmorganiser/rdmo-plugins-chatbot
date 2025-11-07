from utils import get_config, json_to_messages, messages_to_json

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


class SqlStore(BaseStore):
    pass


class SqliteStore(SqlStore):
    pass


class PostgresStore(SqlStore):
    pass


class MysqlStore(BaseStore):

    def __init__(self):
        import MySQLdb
        self.connection = MySQLdb.connect(**config.STORE_DATABASE)
        self.cursor = self.connection.cursor()

    def has_history(self, user_identifier, project_id):
        self.cursor.execute("""
            SELECT count(*) FROM history WHERE user_identifier = %s AND project_id = %s;
        """, [user_identifier, project_id]
        )
        result = self.cursor.fetchone()
        return result[0] > 0

    def get_history(self, user_identifier, project_id):
        self.cursor.execute("""
            SELECT messages FROM history WHERE user_identifier = %s AND project_id = %s;
        """, [user_identifier, project_id]
        )
        result = self.cursor.fetchone()
        return json_to_messages(result[0])

    def set_history(self, user_identifier, project_id, history):
        self.cursor.execute("""
            INSERT INTO history (user_identifier, project_id, messages) VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE messages = VALUES(messages), updated = CURRENT_TIMESTAMP;
        """, [user_identifier, project_id, messages_to_json(history)])
        self.connection.commit()

    def reset_history(self, user_identifier, project_id):
        self.cursor.execute("""
            DELETE FROM history WHERE user_identifier = %s AND project_id = %s;
        """, [user_identifier, project_id]
        )
        self.connection.commit()
