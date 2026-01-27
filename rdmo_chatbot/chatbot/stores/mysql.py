import json

import MySQLdb
from MySQLdb import OperationalError

from ..utils import dicts_to_messages, get_config, messages_to_dicts
from . import BaseStore

config = get_config()

class MysqlStore(BaseStore):

    def __init__(self):
        self.connection = None
        self.cursor = None
        self._connect()
        self.create_table()

    def _connect(self):
        self.connection = MySQLdb.connect(**config.STORE_CONNECTION)
        self.connection.autocommit(True)
        self.cursor = self.connection.cursor()

    def _ensure_connection(self):
        try:
            self.connection.ping(True)
        except Exception:
            self._connect()

    def _execute(self, sql, params=None):
        self._ensure_connection()
        try:
            return self.cursor.execute(sql, params or ())
        except OperationalError as exc:
            if exc.args and exc.args[0] in (2006, 2013):
                self._connect()
                return self.cursor.execute(sql, params or ())
            raise

    def create_table(self):
        self._execute("""
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

    def has_history(self, user_identifier, project_id):
        self._execute("""
            SELECT count(*) FROM history WHERE user_identifier = %s AND project_id = %s;
        """, (user_identifier, project_id)
        )
        result = self.cursor.fetchone()
        return result[0] > 0 if result else False

    def get_history(self, user_identifier, project_id):
        self._execute("""
            SELECT messages FROM history WHERE user_identifier = %s AND project_id = %s;
        """, (user_identifier, project_id)
        )
        result = self.cursor.fetchone()
        return dicts_to_messages(json.loads(result[0])) if result else []

    def set_history(self, user_identifier, project_id, messages):
        self._execute("""
            INSERT INTO history (user_identifier, project_id, messages, created) VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON DUPLICATE KEY UPDATE
                messages = VALUES(messages),
                updated = CURRENT_TIMESTAMP;
        """, (user_identifier, project_id, json.dumps(messages_to_dicts(messages))))

    def reset_history(self, user_identifier, project_id):
        self._execute("""
            DELETE FROM history WHERE user_identifier = %s AND project_id = %s;
        """, [user_identifier, project_id]
        )
