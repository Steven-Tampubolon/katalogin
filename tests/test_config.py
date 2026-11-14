from dataclasses import fields, is_dataclass
from typing import get_type_hints

import pytest

import katalogin
from katalogin.config import PLATFORMS, TONES, ambil_platform, ambil_tone
from katalogin.models import Product


def test_versi_paket() -> None:
    assert katalogin.__version__ == "0.1.0"


def test_konfigurasi_platform() -> None:
    assert PLATFORMS == {
        "shopee": {
            "judul_maks": 255,
            "deskripsi_maks": 3000,
            "tag_maks": 10,
            "hashtag": False,
        },
        "tokopedia": {
            "judul_maks": 70,
            "deskripsi_maks": 2000,
            "tag_maks": 5,
            "hashtag": False,
        },
        "tiktok": {
            "judul_maks": 255,
            "deskripsi_maks": 5000,
            "tag_maks": 5,
            "hashtag": True,
        },
    }


def test_daftar_tone() -> None:
    assert TONES == ("kasual", "profesional", "singkat")


@pytest.mark.parametrize(
    ("nama", "judul_maks", "deskripsi_maks", "tag_maks", "hashtag"),
    [
        ("shopee", 255, 3000, 10, False),
        ("tokopedia", 70, 2000, 5, False),
        ("tiktok", 255, 5000, 5, True),
    ],
)
def test_ambil_platform(
    nama: str,
    judul_maks: int,
    deskripsi_maks: int,
    tag_maks: int,
    hashtag: bool,
) -> None:
    platform = ambil_platform(nama)

    assert platform["judul_maks"] == judul_maks
    assert platform["deskripsi_maks"] == deskripsi_maks
    assert platform["tag_maks"] == tag_maks
    assert platform["hashtag"] is hashtag


def test_ambil_platform_mengabaikan_spasi_dan_huruf_besar() -> None:
    assert ambil_platform(" Shopee ")["judul_maks"] == 255


def test_ambil_platform_mengembalikan_objek_yang_sama() -> None:
    assert ambil_platform("shopee") is PLATFORMS["shopee"]


def test_ambil_platform_menolak_platform_tidak_dikenal() -> None:
    with pytest.raises(ValueError) as galat:
        ambil_platform("LaZaDa")

    assert str(galat.value) == (
        "Platform tidak dikenal: LaZaDa. Pilihan: shopee, tokopedia, tiktok"
    )


@pytest.mark.parametrize("nama", TONES)
def test_ambil_tone(nama: str) -> None:
    assert ambil_tone(nama.upper()) == nama


def test_ambil_tone_mengabaikan_spasi_dan_huruf_besar() -> None:
    assert ambil_tone(" Kasual ") == "kasual"


def test_ambil_tone_menolak_tone_tidak_dikenal() -> None:
    with pytest.raises(ValueError) as galat:
        ambil_tone("x")

    assert str(galat.value) == "Tone tidak dikenal: x. Pilihan: kasual, profesional, singkat"


def test_product_memiliki_field_benar() -> None:
    assert is_dataclass(Product)
    assert [field.name for field in fields(Product)] == [
        "nama",
        "merek",
        "bahan",
        "ukuran",
        "warna",
        "fungsi",
        "fitur",
    ]
    assert get_type_hints(Product) == {
        "nama": str,
        "merek": str | None,
        "bahan": str | None,
        "ukuran": str | None,
        "warna": str | None,
        "fungsi": str | None,
        "fitur": list[str],
    }


def test_product_menggunakan_default_yang_benar() -> None:
    produk = Product(nama="A")

    assert produk.nama == "A"
    assert produk.merek is None
    assert produk.bahan is None
    assert produk.ukuran is None
    assert produk.warna is None
    assert produk.fungsi is None
    assert produk.fitur == []


def test_product_tidak_berbagi_daftar_fitur() -> None:
    produk_kedua = Product(nama="B")
    produk_pertama = Product(nama="A")

    produk_pertama.fitur.append("Adem")

    assert produk_kedua.fitur == []


def test_fixture_kaos(kaos: Product) -> None:
    assert kaos == Product(
        nama="Kaos Polos Pria",
        merek="Oneck",
        bahan="Katun Combed 30s",
        ukuran="L",
        warna="Hitam",
        fungsi="Harian",
        fitur=["Adem", "Tidak Mudah Luntur"],
    )
