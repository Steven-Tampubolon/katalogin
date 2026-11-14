from contextlib import closing

import pytest

from katalogin import db, history
from katalogin.credits import KreditTidakCukup
from katalogin.models import Product
from katalogin.pipeline import generate
from katalogin.service import proses


WAKTU = "2026-11-14T10:30:00+00:00"


@pytest.fixture
def db_path(tmp_path) -> str:
    jalur = str(tmp_path / "katalogin.db")
    db.init_db(jalur)
    return jalur


def hitung_tabel(jalur_db: str) -> dict[str, int]:
    with closing(db.buka(jalur_db)) as koneksi:
        return {
            tabel: koneksi.execute(f"SELECT COUNT(*) FROM {tabel}").fetchone()[0]
            for tabel in ("pengguna", "ledger", "riwayat")
        }


def test_proses_satu_produk_mengurangi_kredit_dan_menyimpan_riwayat(
    db_path, kaos
) -> None:
    proses_hasil = proses(db_path, "andi", [kaos], "shopee", waktu=WAKTU)

    assert proses_hasil.ids == [1]
    assert proses_hasil.sisa_kredit == 4
    assert proses_hasil.hasil[0].judul == generate(kaos, "shopee").judul
    assert hitung_tabel(db_path) == {"pengguna": 1, "ledger": 2, "riwayat": 1}


def test_proses_tiga_produk_menghasilkan_tiga_riwayat(db_path, kaos) -> None:
    daftar = [kaos, Product(nama="Celana Chino"), Product(nama="Topi Baseball")]

    proses_hasil = proses(db_path, "andi", daftar, "shopee", waktu=WAKTU)

    assert proses_hasil.ids == [1, 2, 3]
    assert proses_hasil.sisa_kredit == 2
    assert len(proses_hasil.hasil) == 3
    assert hitung_tabel(db_path) == {"pengguna": 1, "ledger": 2, "riwayat": 3}


def test_proses_kredit_tidak_cukup_membatalkan_seluruh_perubahan(
    db_path, kaos
) -> None:
    with pytest.raises(KreditTidakCukup) as galat:
        proses(db_path, "andi", [kaos] * 6, "shopee", waktu=WAKTU)

    assert galat.value.butuh == 6
    assert galat.value.sisa == 5
    assert hitung_tabel(db_path) == {"pengguna": 0, "ledger": 0, "riwayat": 0}


def test_proses_dengan_produk_invalid_tidak_menulis_database(db_path) -> None:
    with pytest.raises(ValueError, match="^Nama produk wajib diisi$"):
        proses(db_path, "andi", [Product(nama="  ")], "shopee", waktu=WAKTU)

    assert hitung_tabel(db_path) == {"pengguna": 0, "ledger": 0, "riwayat": 0}


def test_proses_dengan_platform_tidak_dikenal_tidak_menulis_database(
    db_path, kaos
) -> None:
    pesan = "^Platform tidak dikenal: lazada\\. Pilihan: shopee, tokopedia, tiktok$"

    with pytest.raises(ValueError, match=pesan):
        proses(db_path, "andi", [kaos], "lazada", waktu=WAKTU)

    assert hitung_tabel(db_path) == {"pengguna": 0, "ledger": 0, "riwayat": 0}


def test_proses_daftar_kosong_tidak_menulis_database(db_path) -> None:
    with pytest.raises(ValueError, match="^Daftar produk kosong$"):
        proses(db_path, "andi", [], "shopee", waktu=WAKTU)

    assert hitung_tabel(db_path) == {"pengguna": 0, "ledger": 0, "riwayat": 0}


def test_proses_membatalkan_transaksi_saat_penyimpanan_riwayat_gagal(
    db_path, kaos, monkeypatch
) -> None:
    simpan_asli = history.simpan
    jumlah_panggilan = 0

    def simpan_gagal(koneksi, user_id, hasil, waktu):
        nonlocal jumlah_panggilan
        jumlah_panggilan += 1
        if jumlah_panggilan == 2:
            raise RuntimeError("Gagal menyimpan riwayat kedua")
        return simpan_asli(koneksi, user_id, hasil, waktu)

    monkeypatch.setattr(history, "simpan", simpan_gagal)
    daftar = [kaos, Product(nama="Celana Chino"), Product(nama="Topi Baseball")]

    with pytest.raises(RuntimeError, match="^Gagal menyimpan riwayat kedua$"):
        proses(db_path, "andi", daftar, "shopee", waktu=WAKTU)

    assert jumlah_panggilan == 2
    assert hitung_tabel(db_path) == {"pengguna": 0, "ledger": 0, "riwayat": 0}
