import json

from .base import BaseStore
from . import config
from ..utils import messages_to_dicts, dicts_to_messages

import psycopg


class PostgresStore(BaseStore):
    def __init__(self):

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
