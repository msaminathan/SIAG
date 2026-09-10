import mysql.connector
import os
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv()


def get_config():
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'database': os.getenv('DB_NAME', 'SIAG'),
        'user': os.getenv('DB_USER', 'siag_user'),
        'password': os.getenv('DB_PASSWORD', ''),
        'autocommit': True,
        'charset': 'utf8mb4',
    }


@contextmanager
def get_connection(dictionary=True):
    cfg = get_config()
    conn = mysql.connector.connect(**cfg, use_pure=True)
    try:
        yield conn
    finally:
        conn.close()


def execute_query(query, params=None, fetch='all', dictionary=True):
    """
    Generic query helper. Returns rows or lastrowid depending on `fetch`.
    fetch: 'all' -> list of dicts/tuples
           'one' -> single dict/tuple or None
           'none' -> None  (INSERT/UPDATE/DELETE)
    """
    with get_connection(dictionary=dictionary) as conn:
        cur = conn.cursor(dictionary=dictionary)
        cur.execute(query, params or ())
        if fetch == 'all':
            result = cur.fetchall()
            return result
        elif fetch == 'one':
            result = cur.fetchone()
            return result
        elif fetch == 'lastid':
            return cur.lastrowid
        else:
            return None


def fetch_all(query, params=None):
    return execute_query(query, params=params, fetch='all')


def fetch_one(query, params=None):
    return execute_query(query, params=params, fetch='one')


def execute_write(query, params=None):
    return execute_query(query, params=params, fetch='none')


def log_activity(user_id, action, entity_type, entity_id=None, details=None):
    execute_write(
        "INSERT INTO activity_log (user_id, action, entity_type, entity_id, details) VALUES (%s, %s, %s, %s, %s)",
        (user_id, action, entity_type, entity_id, details),
    )
