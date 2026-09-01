import os
import psycopg2
import threading
from psycopg2.pool import ThreadedConnectionPool
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()


def get_connection_string():
    return os.environ["SUPABASE_CONNECTION"]


_pool = None
_pool_lock = threading.Lock()


def _get_pool():
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = ThreadedConnectionPool(5, 5, get_connection_string())
    return _pool


@contextmanager
def get_db_connection():
    pool = _get_pool()
    conn = pool.getconn()
    try:
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        finally:
            cur.close()
        pool.putconn(conn)
    except Exception:
        pool.putconn(conn, close=True)
        raise


# Прогреваем пул сразу при импорте модуля, а не при первом реальном
# обращении — чтобы задержка (~15с на 5 соединений) приходилась на
# старт процесса Streamlit, а не на первый клик пользователя.
_get_pool()
