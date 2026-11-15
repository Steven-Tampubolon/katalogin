import dataclasses
import json
import sqlite3

from katalogin.pipeline import Hasil


def simpan(
    conn: sqlite3.Connection, user_id: str, hasil: Hasil, waktu: str
) -> int:
    hasil_json = json.dumps(dataclasses.asdict(hasil), ensure_ascii=False)
    cursor = conn.execute(
        "INSERT INTO riwayat("
        "user_id, dibuat, platform, tone, nama_produk, hasil_json"
        ") VALUES (?, ?, ?, ?, ?, ?)",
        (
            user_id,
            waktu,
            hasil.platform,
            hasil.tone,
            hasil.nama_produk,
            hasil_json,
        ),
    )
    return int(cursor.lastrowid)


def hitung(conn: sqlite3.Connection, user_id: str) -> int:
    baris = conn.execute(
        "SELECT COUNT(*) FROM riwayat WHERE user_id = ?", (user_id,)
    ).fetchone()
    return int(baris[0])


def daftar(
    conn: sqlite3.Connection, user_id: str, limit: int, offset: int
) -> list[dict]:
    baris = conn.execute(
        "SELECT id, dibuat, platform, tone, nama_produk "
        "FROM riwayat WHERE user_id = ? ORDER BY id DESC LIMIT ? OFFSET ?",
        (user_id, limit, offset),
    ).fetchall()
    return [dict(item) for item in baris]


def ambil(
    conn: sqlite3.Connection, user_id: str, riwayat_id: int
) -> dict | None:
    baris = conn.execute(
        "SELECT id, dibuat, hasil_json FROM riwayat WHERE user_id = ? AND id = ?",
        (user_id, riwayat_id),
    ).fetchone()
    if baris is None:
        return None
    return {
        "id": int(baris["id"]),
        "dibuat": baris["dibuat"],
        "hasil": json.loads(baris["hasil_json"]),
    }
