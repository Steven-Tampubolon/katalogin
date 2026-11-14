from dataclasses import fields
from copy import deepcopy

import pytest

from katalogin.descriptions import buat_deskripsi
from katalogin.models import Product
from katalogin.pipeline import Hasil, generate, generate_batch
from katalogin.tags import buat_tags
from katalogin.titles import buat_judul


def test_hasil_memiliki_field_berurutan_yang_diusulkan() -> None:
    assert [field.name for field in fields(Hasil)] == [
        "nama_produk",
        "platform",
        "tone",
        "judul",
        "deskripsi",
        "tags",
        "pelanggaran",
    ]


def test_generate_menghasilkan_konten_sesuai_modul_sebelumnya(kaos) -> None:
    hasil = generate(kaos, "shopee", "kasual")

    assert hasil.nama_produk == "Kaos Polos Pria"
    assert hasil.platform == "shopee"
    assert hasil.tone == "kasual"
    assert hasil.judul == buat_judul(kaos, "shopee")
    assert hasil.deskripsi == buat_deskripsi(kaos, "shopee", "kasual")
    assert hasil.tags == buat_tags(kaos, "shopee")
    assert len(hasil.tags) == 7
    assert hasil.pelanggaran == []


def test_generate_membatasi_tag_tokopedia(kaos) -> None:
    hasil = generate(kaos, "tokopedia")

    assert len(hasil.tags) == 5
    assert hasil.tags == buat_tags(kaos, "tokopedia")


def test_generate_menormalkan_platform_dan_tone(kaos) -> None:
    hasil = generate(kaos, " TikTok ", "Singkat")

    assert hasil.platform == "tiktok"
    assert hasil.tone == "singkat"
    assert hasil.tags
    assert all(tag.startswith("#") for tag in hasil.tags)


def test_generate_membersihkan_kata_terlarang_dari_nama() -> None:
    produk = Product(nama="Kaos Termurah Pria")

    hasil = generate(produk, "shopee")

    assert hasil.nama_produk == "Kaos Pria"
    assert hasil.judul == ["Kaos Pria"]
    assert hasil.pelanggaran == ["termurah"]
    assert hasil.deskripsi == (
        "Halo kak! Kenalin Kaos Pria.\n\nYuk, order sekarang, kak!"
    )


def test_generate_membuang_fitur_kosong_setelah_pembersihan() -> None:
    produk = Product(nama="Kaos", fitur=["Terlaris", "Adem"])

    hasil = generate(produk, "shopee")

    assert hasil.judul == ["Kaos", "Kaos Adem"]
    assert hasil.pelanggaran == ["terlaris"]
    assert "- Fitur: Adem" in hasil.deskripsi
    assert "Terlaris" not in hasil.deskripsi


def test_generate_menggabungkan_pelanggaran_unik_dalam_urutan_kemunculan() -> None:
    produk = Product(
        nama="Kaos Termurah",
        merek="Terbaik",
        fitur=["Terlaris", "Termurah"],
    )

    hasil = generate(produk, "shopee")

    assert hasil.pelanggaran == ["termurah", "terbaik", "terlaris"]


def test_generate_membuat_field_kosong_menjadi_none() -> None:
    produk = Product(nama="Kaos", merek="Terbaik", bahan=" ", fitur=["Adem"])

    hasil = generate(produk, "shopee")

    assert hasil.judul == ["Kaos", "Kaos Adem"]
    assert hasil.deskripsi == (
        "Halo kak! Kenalin Kaos.\n\n"
        "Spesifikasi:\n- Fitur: Adem\n\n"
        "Yuk, order sekarang, kak!"
    )


def test_generate_tidak_mengubah_produk_asli(kaos) -> None:
    salinan = deepcopy(kaos)

    generate(kaos, "shopee")

    assert kaos == salinan


def test_generate_menolak_nama_produk_kosong() -> None:
    with pytest.raises(
        ValueError, match="^Nama produk wajib diisi$"
    ):
        generate(Product(nama="  "), "shopee")


def test_generate_menolak_nama_yang_hanya_terdiri_dari_kata_terlarang() -> None:
    with pytest.raises(
        ValueError,
        match="^Nama produk kosong setelah pembersihan kata terlarang$",
    ):
        generate(Product(nama="Termurah"), "shopee")


def test_generate_memvalidasi_platform_dan_tone_sebelum_produk() -> None:
    with pytest.raises(ValueError, match="^Platform tidak dikenal"):
        generate(Product(nama="  "), "lazada", "kasual")

    with pytest.raises(ValueError, match="^Tone tidak dikenal"):
        generate(Product(nama="  "), "shopee", "serius")


def test_generate_batch_mempertahankan_urutan_produk(kaos) -> None:
    hasil = generate_batch([kaos, Product(nama="Tas")], "shopee")

    assert [item.nama_produk for item in hasil] == [
        "Kaos Polos Pria",
        "Tas",
    ]


@pytest.mark.parametrize(
    ("platform", "tone", "pesan"),
    [
        ("lazada", "kasual", "^Platform tidak dikenal"),
        ("shopee", "serius", "^Tone tidak dikenal"),
    ],
)
def test_generate_batch_memvalidasi_sebelum_memproses_produk(
    platform, tone, pesan
) -> None:
    with pytest.raises(ValueError, match=pesan):
        generate_batch([Product(nama="  ")], platform, tone)


def test_generate_batch_memvalidasi_platform_saat_daftar_kosong() -> None:
    with pytest.raises(ValueError, match="^Platform tidak dikenal"):
        generate_batch([], "lazada")
