import json

import psycopg

from ..utils import dicts_to_messages, get_config, messages_to_dicts
from . import BaseStore

config = get_config()


class PostgresStore(BaseStore):
    def __init__(self):
        self.create_table()

    def connect(self):
        return psycopg.connect(**config.STORE_CONNECTION)

    def create_table(self):
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
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
            connection.commit()

    def has_history(self, user_identifier, project_id):
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT count(*) FROM history WHERE user_identifier = %s AND project_id = %s;
                """, (user_identifier, project_id))
                result = cursor.fetchone()
                return result[0] > 0 if result else False

    def get_history(self, user_identifier, project_id):
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT messages FROM history WHERE user_identifier = %s AND project_id = %s;
                """, (user_identifier, project_id))
                result = cursor.fetchone()
                return dicts_to_messages(result[0]) if result else []

    def set_history(self, user_identifier, project_id, messages):
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO history (user_identifier, project_id, messages, created)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_identifier, project_id) DO UPDATE SET
                        messages = EXCLUDED.messages,
                        updated = CURRENT_TIMESTAMP;
                """, (user_identifier, project_id, json.dumps(messages_to_dicts(messages))))
            connection.commit()

    def reset_history(self, user_identifier, project_id):
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM history WHERE user_identifier = %s AND project_id = %s;
                """, (user_identifier, project_id))
            connection.commit()
