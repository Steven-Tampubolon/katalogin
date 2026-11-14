import dataclasses

import pytest

from katalogin.credits import pastikan_pengguna
from katalogin.db import buka, init_db
from katalogin.history import ambil, daftar, hitung, simpan
from katalogin.pipeline import generate


WAKTU = "2026-11-14T10:30:00+00:00"


@pytest.fixture
def conn(tmp_path):
    db_path = str(tmp_path / "katalogin.db")
    init_db(db_path)
    koneksi = buka(db_path)
    try:
        yield koneksi
    finally:
        koneksi.close()


@pytest.fixture
def hasil(kaos):
    return generate(kaos, "shopee")


def test_simpan_mengembalikan_id_berurutan(conn, hasil) -> None:
    pastikan_pengguna(conn, "andi", WAKTU)

    assert simpan(conn, "andi", hasil, WAKTU) == 1
    assert simpan(conn, "andi", hasil, WAKTU) == 2


def test_ambil_mengembalikan_hasil_lengkap_dan_unicode_utuh(conn, hasil) -> None:
    ensure_pengguna = pastikan_pengguna(conn, "andi", WAKTU)
    assert ensure_pengguna is True

    riwayat_id = simpan(conn, "andi", hasil, WAKTU)
    tersimpan = ambil(conn, "andi", riwayat_id)

    assert set(tersimpan) == {"id", "dibuat", "hasil"}
    assert tersimpan["id"] == riwayat_id
    assert tersimpan["dibuat"] == WAKTU
    assert tersimpan["hasil"] == dataclasses.asdict(hasil)
    assert len(tersimpan["hasil"]["judul"]) == 3

    baris = conn.execute(
        "SELECT hasil_json FROM riwayat WHERE id = ?", (riwayat_id,)
    ).fetchone()
    assert "Tidak Mudah Luntur" in baris["hasil_json"]
    assert "\\u" not in baris["hasil_json"]


def test_ambil_menolak_riwayat_pengguna_lain_dan_id_tidak_ada(conn, hasil) -> None:
    pastikan_pengguna(conn, "andi", WAKTU)
    pastikan_pengguna(conn, "budi", WAKTU)
    riwayat_id = simpan(conn, "andi", hasil, WAKTU)

    assert ambil(conn, "budi", riwayat_id) is None
    assert ambil(conn, "andi", 99) is None


def test_hitung_dan_daftar_memisahkan_riwayat_pengguna(conn, hasil) -> None:
    pastikan_pengguna(conn, "andi", WAKTU)
    pastikan_pengguna(conn, "budi", WAKTU)
    simpan(conn, "andi", hasil, WAKTU)
    simpan(conn, "andi", hasil, WAKTU)
    simpan(conn, "andi", hasil, WAKTU)
    id_budi = simpan(conn, "budi", hasil, WAKTU)

    assert hitung(conn, "andi") == 3
    assert hitung(conn, "budi") == 1

    semua = daftar(conn, "andi", 10, 0)
    assert [item["id"] for item in semua] == [3, 2, 1]
    assert all(
        set(item) == {"id", "dibuat", "platform", "tone", "nama_produk"}
        for item in semua
    )

    halaman = daftar(conn, "andi", 2, 1)
    assert [item["id"] for item in halaman] == [2, 1]

    milik_budi = daftar(conn, "budi", 10, 0)
    assert [item["id"] for item in milik_budi] == [id_budi]
