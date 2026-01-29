import json
import sqlite3
import sys

from ..utils import dicts_to_messages, get_config, messages_to_dicts
from . import BaseStore

config = get_config()


class Sqlite3Store(BaseStore):

    def __init__(self):
        if sys.version_info < (3, 11):
            raise RuntimeError("Sqlite3Store requires Python 3.11 or higher.")

        self.create_table()

    def connect(self):
        return sqlite3.connect(config.STORE_CONNECTION)

    def create_table(self):
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
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
            connection.commit()

    def has_history(self, user_identifier, project_id):
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT count(*) FROM history WHERE user_identifier = ? AND project_id = ?;
                """, (user_identifier, project_id))
                result = cursor.fetchone()
                return result[0] > 0 if result else False

    def get_history(self, user_identifier, project_id):
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT messages FROM history WHERE user_identifier = ? AND project_id = ?;
                """, (user_identifier, project_id))
                result = cursor.fetchone()
                if not result or result[0] is None:
                    return []
                return dicts_to_messages(json.loads(result[0]))

    def set_history(self, user_identifier, project_id, messages):
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO history (user_identifier, project_id, messages) VALUES (?, ?, ?)
                    ON CONFLICT (user_identifier, project_id) DO UPDATE SET
                        messages = EXCLUDED.messages,
                        updated = CURRENT_TIMESTAMP;
                """, (user_identifier, project_id, json.dumps(messages_to_dicts(messages))))
            connection.commit()

    def reset_history(self, user_identifier, project_id):
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM history WHERE user_identifier = ? AND project_id = ?;
                """, (user_identifier, project_id))
            connection.commit()
