import os

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://settle:settle_dev_password@postgres:5432/settle",
)


pool = ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=1,
    max_size=5,
    timeout=3,
    kwargs={"row_factory": dict_row},
)


def get_connection():
    return pool.connection()


def check_database():
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()

        return True

    except psycopg.Error:
        return False