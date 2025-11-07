from utils import get_config

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


class MysqlStore(SqlStore):
    pass


class PostgresStore(SqlStore):
    pass
