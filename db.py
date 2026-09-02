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


def warm_up_pool():
    """Явно прогревает пул соединений. Вызывается один раз при старте
    Streamlit-приложения (rag_app.py) — НЕ автоматически при импорте
    модуля, чтобы conftest.py успевал переключить SUPABASE_CONNECTION
    на тестовую БД до первого реального подключения."""
    _get_pool()


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
