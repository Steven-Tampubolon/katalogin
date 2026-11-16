from katalogin.web.klien_api import ApiError
from katalogin.web.tampilan import (
    PLATFORM_OPSI,
    TONE_OPSI,
    baris_hasil_csv,
    baris_riwayat,
    hitung_karakter,
    pesan_galat,
    tags_ke_teks,
)


def test_opsi_platform_dan_tone_sesuai_konfigurasi() -> None:
    assert PLATFORM_OPSI == ["shopee", "tokopedia", "tiktok"]
    assert TONE_OPSI == ["kasual", "profesional", "singkat"]


def test_hitung_karakter_menampilkan_jumlah_dan_batas() -> None:
    assert hitung_karakter("abc", 70) == "3/70 karakter"


def test_tags_ke_teks_menggabungkan_tag_dengan_koma() -> None:
    assert tags_ke_teks(["a", "b"]) == "a, b"


def test_tags_ke_teks_kosong_menghasilkan_teks_kosong() -> None:
    assert tags_ke_teks([]) == ""


def test_pesan_galat_401_menyarankan_pengisian_id_pengguna() -> None:
    assert pesan_galat(ApiError(401, "x")) == "ID pengguna belum diisi."


def test_pesan_galat_402_menambahkan_petunjuk_kredit_habis() -> None:
    galat = ApiError(402, "Kredit tidak cukup: butuh 1, tersisa 0")

    assert pesan_galat(galat) == (
        "Kredit tidak cukup: butuh 1, tersisa 0. "
        "Kredit habis; hubungi admin untuk menambah kredit."
    )


def test_pesan_galat_413_menyarankan_memperkecil_masukan() -> None:
    galat = ApiError(413, "Permintaan terlalu besar")

    assert pesan_galat(galat) == (
        "Berkas atau teks terlalu besar. Perkecil lalu coba lagi."
    )


def test_pesan_galat_status_lain_memakai_detail_apa_adanya() -> None:
    assert pesan_galat(ApiError(400, "Nama produk tidak ditemukan")) == (
        "Nama produk tidak ditemukan"
    )
    assert pesan_galat(ApiError(502, "Layanan AI gagal: kuota habis")) == (
        "Layanan AI gagal: kuota habis"
    )
    assert pesan_galat(ApiError(0, "Tidak bisa terhubung ke server API")) == (
        "Tidak bisa terhubung ke server API"
    )


def test_baris_riwayat_memetakan_kolom_tampilan() -> None:
    item = {
        "id": 3,
        "dibuat": "2026-11-14T10:30:00+00:00",
        "platform": "shopee",
        "tone": "kasual",
        "nama_produk": "Kaos",
    }

    assert baris_riwayat([item]) == [
        {
            "ID": 3,
            "Waktu": "2026-11-14T10:30:00+00:00",
            "Platform": "shopee",
            "Tone": "kasual",
            "Produk": "Kaos",
        }
    ]


def test_baris_hasil_csv_mengisi_tiga_kolom_judul_dan_meringkas_kolom_teks() -> None:
    hasil = {
        "nama_produk": "Kaos",
        "judul": ["A", "B"],
        "tags": ["x", "y"],
        "pelanggaran": ["termurah", "terbaik"],
    }

    assert baris_hasil_csv([hasil]) == [
        {
            "Produk": "Kaos",
            "Judul 1": "A",
            "Judul 2": "B",
            "Judul 3": "",
            "Tag": "x, y",
            "Peringatan": "termurah, terbaik",
        }
    ]
