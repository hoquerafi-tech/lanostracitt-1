import os
import pymysql
from pymysql.cursors import DictCursor

# Configure remote database credentials through environment variables.
HOST = os.getenv("DB_HOST", "localhost")
PORT = int(os.getenv("DB_PORT", "3306"))
USER = os.getenv("DB_USER", "root")
PASSWORD = os.getenv("DB_PASS", "")
NAME = os.getenv("DB_NAME", "InsiemePerMilano")
USA_SSL = os.getenv("DB_SSL", "0") == "1"
CA_FILE = os.getenv("DB_SSL_CA")


def get_conn():
    """Apre una nuova connessione al database."""
    extra = {}
    if USA_SSL:
        extra["ssl"] = {"ca": CA_FILE} if CA_FILE else {"check_hostname": False}
    return pymysql.connect(
        host=HOST, port=PORT, user=USER, password=PASSWORD, database=NAME,
        charset="utf8mb4", cursorclass=DictCursor, autocommit=False, **extra)


def query(sql, params=(), one=False):
    """SELECT: restituisce lista di dizionari (o uno solo)."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone() if one else cur.fetchall()
    finally:
        conn.close()


def execute(sql, params=()):
    """INSERT/UPDATE/DELETE: restituisce l'id inserito."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()