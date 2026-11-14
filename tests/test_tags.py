import pytest

from katalogin.models import Product
from katalogin.tags import buat_tags


def test_buat_tags_menghasilkan_semua_kandidat_shopee(kaos) -> None:
    assert buat_tags(kaos, "shopee") == [
        "kaos polos pria",
        "oneck kaos polos pria",
        "kaos polos pria hitam",
        "kaos polos pria katun combed 30s",
        "kaos polos pria harian",
        "adem",
        "tidak mudah luntur",
    ]


def test_buat_tags_membatasi_jumlah_tag_tokopedia(kaos) -> None:
    assert buat_tags(kaos, "tokopedia") == [
        "kaos polos pria",
        "oneck kaos polos pria",
        "kaos polos pria hitam",
        "kaos polos pria katun combed 30s",
        "kaos polos pria harian",
    ]


def test_buat_tags_membuat_hashtag_tiktok(kaos) -> None:
    assert buat_tags(kaos, "tiktok") == [
        "#kaospolospria",
        "#oneckkaospolospria",
        "#kaospolospriahitam",
        "#kaospolospriakatuncombed30s",
        "#kaospolospriaharian",
    ]


def test_buat_tags_melewati_bagian_kosong_dan_duplikat() -> None:
    produk = Product(
        nama="Kaos",
        merek="",
        warna=None,
        bahan=" ",
        fungsi="",
        fitur=["", "Adem", "adem"],
    )

    assert buat_tags(produk, "shopee") == ["kaos", "adem"]


def test_buat_tags_membuat_hashtag_tanpa_karakter_khusus() -> None:
    produk = Product(nama="Kaos #01!", merek="A&B")

    assert buat_tags(produk, "tiktok") == ["#kaos01", "#abkaos01"]


def test_buat_tags_menolak_platform_tidak_dikenal(kaos) -> None:
    with pytest.raises(ValueError, match="^Platform tidak dikenal"):
        buat_tags(kaos, "unknown")
