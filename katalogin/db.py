import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator


SKEMA = """
CREATE TABLE IF NOT EXISTS pengguna (
  user_id TEXT PRIMARY KEY,
  kredit INTEGER NOT NULL CHECK (kredit >= 0),
  dibuat TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ledger (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL REFERENCES pengguna(user_id),
  delta INTEGER NOT NULL,
  alasan TEXT NOT NULL,
  dibuat TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS riwayat (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL REFERENCES pengguna(user_id),
  dibuat TEXT NOT NULL,
  platform TEXT NOT NULL,
  tone TEXT NOT NULL,
  nama_produk TEXT NOT NULL,
  hasil_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_riwayat_user ON riwayat(user_id, id);
"""


def buka(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=10)
    conn.isolation_level = None
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str) -> None:
    conn = buka(db_path)
    try:
        conn.executescript(SKEMA)
    finally:
        conn.close()


@contextmanager
def transaksi(conn: sqlite3.Connection) -> Iterator[None]:
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield
    except BaseException:
        conn.rollback()
        raise
    else:
        conn.commit()


def sekarang() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
