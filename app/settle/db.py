import os

import psycopg
from psycopg.rows import dict_row


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://settle:settle_dev_password@postgres:5432/settle",
)


def get_connection():
    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row,
    )