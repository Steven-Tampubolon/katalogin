import pytest

from katalogin.config import PLATFORMS
from katalogin.descriptions import buat_deskripsi
from katalogin.models import Product


def test_buat_deskripsi_kasual_sesuai_acceptance(kaos) -> None:
    assert buat_deskripsi(kaos, "shopee", "kasual") == (
        "Halo kak! Kenalin Oneck Kaos Polos Pria.\n\n"
        "Spesifikasi:\n"
        "- Bahan: Katun Combed 30s\n"
        "- Ukuran: L\n"
        "- Warna: Hitam\n"
        "- Fungsi: Harian\n"
        "- Fitur: Adem, Tidak Mudah Luntur\n\n"
        "Yuk, order sekarang, kak!"
    )


def test_buat_deskripsi_profesional_menggunakan_hook_dan_cta_tersendiri(kaos) -> None:
    assert buat_deskripsi(kaos, "shopee", "profesional") == (
        "Oneck Kaos Polos Pria. Berikut spesifikasi produk.\n\n"
        "Spesifikasi:\n"
        "- Bahan: Katun Combed 30s\n"
        "- Ukuran: L\n"
        "- Warna: Hitam\n"
        "- Fungsi: Harian\n"
        "- Fitur: Adem, Tidak Mudah Luntur\n\n"
        "Silakan lakukan pemesanan atau hubungi kami untuk informasi lebih lanjut."
    )


def test_buat_deskripsi_singkat_menggunakan_hook_dan_cta_tersingkat(kaos) -> None:
    hasil = buat_deskripsi(kaos, "shopee", "singkat")

    assert hasil.startswith("Oneck Kaos Polos Pria.\n\nSpesifikasi:")
    assert hasil.endswith("\n\nOrder sekarang.")


def test_buat_deskripsi_menghapus_blok_spesifikasi_bila_tidak_ada_isi() -> None:
    produk = Product(nama="Kaos")

    assert buat_deskripsi(produk, "shopee", "kasual") == (
        "Halo kak! Kenalin Kaos.\n\nYuk, order sekarang, kak!"
    )


def test_buat_deskripsi_hanya_memuat_spesifikasi_yang_terisi() -> None:
    produk = Product(
        nama="Kaos",
        merek=None,
        bahan="Katun",
        ukuran=None,
        warna=" ",
        fungsi=None,
        fitur=["Adem"],
    )

    assert buat_deskripsi(produk, "shopee", "singkat") == (
        "Kaos.\n\nSpesifikasi:\n- Bahan: Katun\n- Fitur: Adem\n\nOrder sekarang."
    )


def test_buat_deskripsi_memotong_pada_batas_kata(kaos, monkeypatch) -> None:
    monkeypatch.setitem(PLATFORMS["tokopedia"], "deskripsi_maks", 60)

    hasil = buat_deskripsi(kaos, "tokopedia", "singkat")

    assert len(hasil) <= 60
    assert hasil == (
        "Oneck Kaos Polos Pria.\n\nSpesifikasi:\n- Bahan: Katun Combed"
    )


def test_buat_deskripsi_menolak_platform_tidak_dikenal(kaos) -> None:
    with pytest.raises(ValueError, match="^Platform tidak dikenal"):
        buat_deskripsi(kaos, "unknown", "kasual")


def test_buat_deskripsi_menolak_tone_tidak_dikenal(kaos) -> None:
    with pytest.raises(ValueError, match="^Tone tidak dikenal"):
        buat_deskripsi(kaos, "shopee", "unknown")
