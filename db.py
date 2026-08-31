import os
import psycopg2
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()


def get_connection_string():
    return os.environ["SUPABASE_CONNECTION"]


@contextmanager
def get_db_connection():
    conn = psycopg2.connect(get_connection_string())
    try:
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        finally:
            cur.close()
    finally:
        conn.close()
