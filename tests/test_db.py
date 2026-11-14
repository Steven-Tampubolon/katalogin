import re
import sqlite3

import pytest

from katalogin.db import buka, init_db, sekarang, transaksi


def test_buka_mengatur_koneksi_sqlite(tmp_path) -> None:
    conn = buka(str(tmp_path / "katalogin.db"))

    try:
        assert conn.isolation_level is None
        assert conn.row_factory is sqlite3.Row
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert conn.execute("SELECT 1 AS nilai").fetchone()["nilai"] == 1
    finally:
        conn.close()


def test_init_db_membuat_skema_dan_aman_dipanggil_berulang(tmp_path) -> None:
    db_path = str(tmp_path / "katalogin.db")

    init_db(db_path)
    init_db(db_path)

    conn = buka(db_path)
    try:
        objek = conn.execute(
            "SELECT type, name FROM sqlite_master WHERE name IN (?, ?, ?, ?)",
            ("pengguna", "ledger", "riwayat", "idx_riwayat_user"),
        ).fetchall()
    finally:
        conn.close()

    assert {(baris["type"], baris["name"]) for baris in objek} == {
        ("table", "pengguna"),
        ("table", "ledger"),
        ("table", "riwayat"),
        ("index", "idx_riwayat_user"),
    }


def test_kredit_negatif_ditolak(tmp_path) -> None:
    init_db(str(tmp_path / "katalogin.db"))
    conn = buka(str(tmp_path / "katalogin.db"))

    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO pengguna(user_id, kredit, dibuat) VALUES ('a', -1, 'x')"
            )
    finally:
        conn.close()


def test_ledger_menolak_pengguna_yang_tidak_ada(tmp_path) -> None:
    init_db(str(tmp_path / "katalogin.db"))
    conn = buka(str(tmp_path / "katalogin.db"))

    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO ledger(user_id, delta, alasan, dibuat) "
                "VALUES ('tidak-ada', 1, 'x', 'x')"
            )
    finally:
        conn.close()


def test_transaksi_membatalkan_baris_bila_blok_gagal(tmp_path) -> None:
    init_db(str(tmp_path / "katalogin.db"))
    conn = buka(str(tmp_path / "katalogin.db"))

    try:
        with pytest.raises(RuntimeError, match="gagal"):
            with transaksi(conn):
                conn.execute(
                    "INSERT INTO pengguna(user_id, kredit, dibuat) VALUES ('a', 5, 'x')"
                )
                raise RuntimeError("gagal")

        assert conn.execute("SELECT COUNT(*) FROM pengguna").fetchone()[0] == 0
    finally:
        conn.close()


def test_transaksi_menyimpan_baris_bila_blok_selesai_normal(tmp_path) -> None:
    db_path = str(tmp_path / "katalogin.db")
    init_db(db_path)
    conn = buka(db_path)

    try:
        with transaksi(conn):
            conn.execute(
                "INSERT INTO pengguna(user_id, kredit, dibuat) VALUES ('a', 5, 'x')"
            )
    finally:
        conn.close()

    conn_lain = buka(db_path)
    try:
        baris = conn_lain.execute(
            "SELECT kredit FROM pengguna WHERE user_id = 'a'"
        ).fetchone()
    finally:
        conn_lain.close()

    assert baris["kredit"] == 5


def test_sekarang_menghasilkan_waktu_utc_dengan_format_yang_dipersyaratkan() -> None:
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+00:00", sekarang())
