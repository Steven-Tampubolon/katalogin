import pytest

from katalogin.credits import (
    KREDIT_GRATIS,
    KreditTidakCukup,
    pastikan_pengguna,
    kurangi,
    saldo,
    tambah,
)
from katalogin.db import buka, init_db


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


def test_pastikan_pengguna_membuat_pengguna_dan_ledger_gratis(conn) -> None:
    assert KREDIT_GRATIS == 5
    assert pastikan_pengguna(conn, "andi", WAKTU) is True
    assert pastikan_pengguna(conn, "andi", WAKTU) is False

    assert saldo(conn, "andi") == 5
    ledger = conn.execute(
        "SELECT delta, alasan FROM ledger WHERE user_id = ? ORDER BY id",
        ("andi",),
    ).fetchall()
    assert [(baris["delta"], baris["alasan"]) for baris in ledger] == [
        (5, "gratis_awal")
    ]


def test_saldo_pengguna_yang_tidak_ada_adalah_nol(conn) -> None:
    assert saldo(conn, "tidak-ada") == 0


def test_kurangi_kredit_mencatat_ledger_dan_mengembalikan_saldo_baru(conn) -> None:
    pastikan_pengguna(conn, "andi", WAKTU)

    assert kurangi(conn, "andi", 2, "generate", WAKTU) == 3
    assert saldo(conn, "andi") == 3

    ledger = conn.execute(
        "SELECT delta, alasan FROM ledger WHERE user_id = ? ORDER BY id",
        ("andi",),
    ).fetchall()
    assert [(baris["delta"], baris["alasan"]) for baris in ledger] == [
        (5, "gratis_awal"),
        (-2, "generate"),
    ]


def test_kurangi_melempar_kredit_tidak_cukup_tanpa_mengubah_saldo(conn) -> None:
    pastikan_pengguna(conn, "andi", WAKTU)
    kurangi(conn, "andi", 2, "generate", WAKTU)

    with pytest.raises(KreditTidakCukup) as galat:
        kurangi(conn, "andi", 4, "generate", WAKTU)

    assert galat.value.butuh == 4
    assert galat.value.sisa == 3
    assert str(galat.value) == "Kredit tidak cukup: butuh 4, tersisa 3"
    assert saldo(conn, "andi") == 3


@pytest.mark.parametrize("jumlah", [0, -1])
def test_kurangi_menolak_jumlah_bukan_positif(conn, jumlah: int) -> None:
    pastikan_pengguna(conn, "andi", WAKTU)

    with pytest.raises(ValueError, match="^Jumlah harus lebih dari 0$"):
        kurangi(conn, "andi", jumlah, "x", WAKTU)


def test_tambah_kredit_mencatat_ledger_dan_mengembalikan_saldo_baru(conn) -> None:
    pastikan_pengguna(conn, "andi", WAKTU)
    kurangi(conn, "andi", 2, "generate", WAKTU)

    assert tambah(conn, "andi", 10, "topup", WAKTU) == 13
    assert saldo(conn, "andi") == 13

    ledger = conn.execute(
        "SELECT delta, alasan FROM ledger WHERE user_id = ? ORDER BY id",
        ("andi",),
    ).fetchall()
    assert [(baris["delta"], baris["alasan"]) for baris in ledger] == [
        (5, "gratis_awal"),
        (-2, "generate"),
        (10, "topup"),
    ]


def test_tambah_melempar_untuk_pengguna_yang_tidak_ada(conn) -> None:
    with pytest.raises(ValueError, match="^Pengguna tidak ditemukan$"):
        tambah(conn, "zzz", 1, "topup", WAKTU)


@pytest.mark.parametrize("jumlah", [0, -1])
def test_tambah_menolak_jumlah_bukan_positif(conn, jumlah: int) -> None:
    pastikan_pengguna(conn, "andi", WAKTU)

    with pytest.raises(ValueError, match="^Jumlah harus lebih dari 0$"):
        tambah(conn, "andi", jumlah, "x", WAKTU)


def test_total_delta_ledger_sama_dengan_saldo(conn) -> None:
    pastikan_pengguna(conn, "andi", WAKTU)
    kurangi(conn, "andi", 2, "generate", WAKTU)
    tambah(conn, "andi", 10, "topup", WAKTU)

    total = conn.execute(
        "SELECT SUM(delta) FROM ledger WHERE user_id = ?", ("andi",)
    ).fetchone()[0]

    assert total == saldo(conn, "andi")
