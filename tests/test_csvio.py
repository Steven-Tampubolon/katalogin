import csv
from io import StringIO

import pytest

from katalogin.csvio import baca_csv, ekspor_csv
from katalogin.pipeline import Hasil, generate


def test_baca_csv_membaca_kolom_dan_fitur_pemisah_pipe() -> None:
    teks = (
        "nama,merek,bahan,ukuran,warna,fungsi,fitur\n"
        "kaos polos pria,Oneck,katun,xl,hitam,harian,adem|tidak mudah luntur"
    )

    produk = baca_csv(teks)[0]

    assert produk.nama == "Kaos Polos Pria"
    assert produk.merek == "Oneck"
    assert produk.bahan == "Katun"
    assert produk.ukuran == "XL"
    assert produk.warna == "Hitam"
    assert produk.fungsi == "Harian"
    assert produk.fitur == ["Adem", "Tidak Mudah Luntur"]


def test_baca_csv_mendukung_delimiter_semicolon() -> None:
    teks = (
        "nama;merek;bahan;ukuran;warna;fungsi;fitur\n"
        "kaos polos pria;Oneck;katun;xl;hitam;harian;adem|tidak mudah luntur"
    )

    produk = baca_csv(teks)[0]

    assert produk.nama == "Kaos Polos Pria"
    assert produk.merek == "Oneck"
    assert produk.bahan == "Katun"
    assert produk.ukuran == "XL"
    assert produk.warna == "Hitam"
    assert produk.fungsi == "Harian"
    assert produk.fitur == ["Adem", "Tidak Mudah Luntur"]


def test_baca_csv_membuang_bom_dan_menormalkan_header() -> None:
    teks = "\ufeff NAMA ,Merek,Per steered\nKaos,Oneck,diabaikan"

    produk = baca_csv(teks)[0]

    assert produk.nama == "Kaos"
    assert produk.merek == "Oneck"


def test_baca_csv_mengubah_sel_kosong_menjadi_none() -> None:
    produk = baca_csv("nama,merek,bahan,fitur\nKaos,,,")[0]

    assert produk.nama == "Kaos"
    assert produk.merek is None
    assert produk.bahan is None
    assert produk.fitur == []


def test_baca_csv_memisahkan_fitur_dan_membuang_item_kosong() -> None:
    produk = baca_csv("nama,fitur\nKaos,adem||tidak mudah luntur")[0]

    assert produk.fitur == ["Adem", "Tidak Mudah Luntur"]


@pytest.mark.parametrize("teks", ["", "   \n\t "])
def test_baca_csv_menolak_csv_kosong(teks: str) -> None:
    with pytest.raises(ValueError, match="^CSV kosong$"):
        baca_csv(teks)


def test_baca_csv_menolak_kolom_nama_yang_hilang() -> None:
    with pytest.raises(ValueError, match="^Kolom 'nama' wajib ada$"):
        baca_csv("merek\nOneck")


def test_baca_csv_menolak_nama_kosong_dengan_nomor_baris_benar() -> None:
    with pytest.raises(ValueError, match="^Baris 3: kolom 'nama' kosong$"):
        baca_csv("nama,merek\nKaos,Oneck\n,Zzz\n")


def test_baca_csv_menghitung_baris_kosong_dalam_nomor_baris() -> None:
    with pytest.raises(ValueError, match="^Baris 3: kolom 'nama' kosong$"):
        baca_csv("nama,merek\n\n,Zzz")


def test_baca_csv_menerima_tepat_20_baris_data() -> None:
    teks = "nama\n" + "".join(f"Produk {nomor}\n" for nomor in range(1, 21))

    assert len(baca_csv(teks)) == 20


def test_baca_csv_menolak_lebih_dari_20_baris_data() -> None:
    teks = "nama\n" + "".join(f"Produk {nomor}\n" for nomor in range(1, 22))

    with pytest.raises(ValueError, match="^Maksimum 20 baris, ditemukan 21$"):
        baca_csv(teks)


def test_ekspor_csv_menghasilkan_header_dan_hasil_pipeline(kaos) -> None:
    hasil = generate(kaos, "shopee")

    teks = ekspor_csv([hasil])
    baris = list(csv.reader(StringIO(teks)))

    assert baris[0] == [
        "nama_produk",
        "platform",
        "tone",
        "judul_1",
        "judul_2",
        "judul_3",
        "deskripsi",
        "tags",
        "peringatan",
    ]
    assert baris[1][0] == hasil.nama_produk
    assert baris[1][1] == hasil.platform
    assert baris[1][2] == hasil.tone
    assert baris[1][3] == hasil.judul[0]
    assert baris[1][6] == hasil.deskripsi
    assert baris[1][7] == ", ".join(hasil.tags)
    assert baris[1][8] == ""


def test_ekspor_csv_mengisi_judul_kurang_dan_menggabungkan_daftar() -> None:
    hasil = Hasil(
        nama_produk="Kaos",
        platform="shopee",
        tone="kasual",
        judul=["Kaos Pria"],
        deskripsi="Deskripsi\nmultiline",
        tags=["kaos", "pria"],
        pelanggaran=["terbaik", "terlaris"],
    )

    baris = list(csv.reader(StringIO(ekspor_csv([hasil]))))

    assert baris[1][3:6] == ["Kaos Pria", "", ""]
    assert baris[1][7] == "kaos, pria"
    assert baris[1][8] == "terbaik; terlaris"


def test_ekspor_csv_daftar_kosong_hanya_menghasilkan_header() -> None:
    assert ekspor_csv([]) == (
        "nama_produk,platform,tone,judul_1,judul_2,judul_3,deskripsi,tags,"
        "peringatan\n"
    )
