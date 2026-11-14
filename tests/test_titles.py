import pytest

from katalogin.models import Product
from katalogin.titles import buat_judul


def test_buat_judul_menghasilkan_tiga_variasi_untuk_fixture_kaos(kaos) -> None:
    assert buat_judul(kaos, "shopee") == [
        "Oneck Kaos Polos Pria Katun Combed 30s L",
        "Kaos Polos Pria Oneck Hitam Katun Combed 30s",
        "Oneck Kaos Polos Pria Hitam L Adem",
    ]


def test_buat_judul_melewati_atribut_kosong() -> None:
    produk = Product(
        nama="Kaos",
        merek="",
        bahan=" ",
        ukuran=None,
        warna="",
        fitur=[" "],
    )

    assert buat_judul(produk, "shopee") == ["Kaos"]


def test_buat_judul_menghapus_duplikat_tanpa_mempertahankan_kapitalisasi() -> None:
    produk = Product(nama="Kaos", merek="kaos")

    assert buat_judul(produk, "shopee") == ["kaos Kaos"]


def test_buat_judul_memotong_pada_batas_kata_tokopedia() -> None:
    produk = Product(
        nama="Kaos Polos Pria Lengan Pendek Katun Combed 30s Premium Quality Oversize",
        merek="Oneck",
        bahan="Katun Combed 30s",
        ukuran="XL",
    )
    judul_penuh = [
        "Oneck Kaos Polos Pria Lengan Pendek Katun Combed 30s Premium Quality Oversize Katun Combed 30s XL",
        "Kaos Polos Pria Lengan Pendek Katun Combed 30s Premium Quality Oversize Oneck Katun Combed 30s",
        "Oneck Kaos Polos Pria Lengan Pendek Katun Combed 30s Premium Quality Oversize XL",
    ]

    hasil = buat_judul(produk, "tokopedia")

    assert hasil == [
        "Oneck Kaos Polos Pria Lengan Pendek Katun Combed 30s Premium Quality",
        "Kaos Polos Pria Lengan Pendek Katun Combed 30s Premium Quality",
    ]
    assert all(len(judul) <= 70 for judul in hasil)
    for judul in hasil:
        assert any(
            judul == penuh[: len(judul)]
            and (len(judul) == len(penuh) or penuh[len(judul)] == " ")
            for penuh in judul_penuh
        )


def test_buat_judul_menolak_platform_tidak_dikenal(kaos) -> None:
    with pytest.raises(ValueError, match="^Platform tidak dikenal"):
        buat_judul(kaos, "unknown")
