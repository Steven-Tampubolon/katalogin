import csv

import pytest

from katalogin.cli import main

TEKS_KAOS = (
    "KAOS POLOS PRIA\n"
    "Brand: Oneck\n"
    "bhn: ktn combed 30s\n"
    "uk: L\n"
    "wrn: htm\n"
    "kegunaan: harian\n"
    "keunggulan: adem, tidak mudah luntur"
)

CSV_DUA_PRODUK = (
    "nama,merek,bahan\n"
    "Kaos Polos Pria,Oneck,Katun Combed 30s\n"
    "Celana Pendek Pria,ABC,Katun\n"
)


@pytest.fixture
def berkas_kaos(tmp_path):
    jalur = tmp_path / "kaos.txt"
    jalur.write_text(TEKS_KAOS, encoding="utf-8")
    return str(jalur)


def test_main_berkas_teks_mencetak_hasil_dan_kembali_nol(capsys, berkas_kaos):
    kode = main(["--platform", "shopee", "--input", berkas_kaos])

    tangkap = capsys.readouterr()
    baris = tangkap.out.splitlines()
    assert kode == 0
    assert tangkap.err == ""
    assert "== Kaos Polos Pria ==" in baris
    assert "Platform: shopee | Tone: kasual" in baris
    assert "Judul 1: Oneck Kaos Polos Pria Katun Combed 30s L" in baris
    assert any(item.startswith("Tag: kaos polos pria, oneck kaos polos pria") for item in baris)
    assert any(item.startswith("Deskripsi:") for item in baris)
    assert not any(item.startswith("Peringatan:") for item in baris)


def test_main_mendukung_tone_pilihan(capsys, berkas_kaos):
    kode = main(["--platform", "tokopedia", "--tone", "profesional", "--input", berkas_kaos])

    tangkap = capsys.readouterr()
    assert kode == 0
    assert "Platform: tokopedia | Tone: profesional" in tangkap.out.splitlines()


def test_main_melaporkan_peringatan_kata_terlarang(capsys, tmp_path):
    jalur = tmp_path / "kaos_termurah.txt"
    jalur.write_text(TEKS_KAOS + "\nfitur: Termurah", encoding="utf-8")

    kode = main(["--platform", "shopee", "--input", str(jalur)])

    tangkap = capsys.readouterr()
    assert kode == 0
    assert "Peringatan: termurah" in tangkap.out.splitlines()


def test_main_csv_dengan_out_menyimpan_berkas_dan_mencetak_tersimpan(capsys, tmp_path):
    jalur = tmp_path / "produk.csv"
    jalur.write_text(CSV_DUA_PRODUK, encoding="utf-8")
    jalur_hasil = tmp_path / "hasil.csv"

    kode = main(
        ["--platform", "tokopedia", "--input", str(jalur), "--out", str(jalur_hasil)]
    )

    tangkap = capsys.readouterr()
    assert kode == 0
    assert "Tersimpan:" in tangkap.out
    assert "(2 produk)" in tangkap.out
    with open(jalur_hasil, "r", encoding="utf-8", newline="") as berkas:
        baris = list(csv.reader(berkas))
    assert len(baris) == 3
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
    assert baris[1][0] == "Kaos Polos Pria"
    assert baris[2][0] == "Celana Pendek Pria"


def test_main_csv_tanpa_out_mencetak_blok_dipisah_baris_kosong(capsys, tmp_path):
    jalur = tmp_path / "produk.csv"
    jalur.write_text(CSV_DUA_PRODUK, encoding="utf-8")

    kode = main(["--platform", "shopee", "--input", str(jalur)])

    tangkap = capsys.readouterr()
    assert kode == 0
    assert "== Kaos Polos Pria ==" in tangkap.out.splitlines()
    assert "== Celana Pendek Pria ==" in tangkap.out.splitlines()
    assert "\n\n== Celana Pendek Pria ==" in tangkap.out


def test_main_berkas_tidak_ada_kembali_satu_dan_stderr_galat(capsys, tmp_path):
    kode = main(["--platform", "shopee", "--input", str(tmp_path / "hilang.txt")])

    tangkap = capsys.readouterr()
    assert kode == 1
    assert tangkap.err.startswith("GALAT:")


def test_main_tanpa_nama_produk_kembali_satu(capsys, tmp_path):
    jalur = tmp_path / "tanpa_nama.txt"
    jalur.write_text("merek: Oneck", encoding="utf-8")

    kode = main(["--platform", "shopee", "--input", str(jalur)])

    tangkap = capsys.readouterr()
    assert kode == 1
    assert "GALAT: Nama produk tidak ditemukan" in tangkap.err


def test_main_platform_tidak_valid_memicu_systemexit_dua(berkas_kaos):
    with pytest.raises(SystemExit) as info:
        main(["--platform", "lazada", "--input", berkas_kaos])

    assert info.value.code == 2
