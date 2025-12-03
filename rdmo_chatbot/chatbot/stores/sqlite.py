import json

from .base import BaseStore
from . import config

import sqlite3

from ..utils import dicts_to_messages, messages_to_dicts


class Sqlite3Store(BaseStore):

    def __init__(self):
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
        if not result or result[0] is None:
            return []
        return dicts_to_messages(json.loads(result[0]))

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
