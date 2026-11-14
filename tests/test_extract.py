import pytest

from katalogin.extract import ekstrak_teks, perluas_singkatan


@pytest.mark.parametrize(
    ("masuk", "harapan"),
    [
        ("Kaos pjg lgn pdk", "Kaos panjang lengan pendek"),
        ("KTN Pth.", "katun putih."),
        ("pthx", "pthx"),
        ("BHN mrh htm", "bahan merah hitam"),
    ],
)
def test_perluas_singkatan(masuk: str, harapan: str) -> None:
    assert perluas_singkatan(masuk) == harapan


def test_ekstrak_teks_menurkuti_semua_label(kaos) -> None:
    teks = (
        "KAOS POLOS PRIA\n"
        "Brand: Oneck\n"
        "bhn: ktn combed 30s\n"
        "uk: L\n"
        "wrn: htm\n"
        "kegunaan: harian\n"
        "keunggulan: adem, tidak mudah luntur"
    )

    assert ekstrak_teks(teks) == kaos


@pytest.mark.parametrize(
    ("teks", "nilai"),
    [
        ("produk: Kaos Pria", "Kaos Pria"),
        ("barang = Kaos Pria", "Kaos Pria"),
        ("nm: Kaos Pria", "Kaos Pria"),
    ],
)
def test_ekstrak_teks_mengenali_alias_label_nama(teks: str, nilai: str) -> None:
    assert ekstrak_teks(teks).nama == nilai


def test_ekstrak_teks_menggunakan_baris_tanpa_label_sebagai_nama() -> None:
    produk = ekstrak_teks("warna: Hitam\nKaos Polos Pria\nbahan: Katun")

    assert produk.nama == "Kaos Polos Pria"
    assert produk.warna == "Hitam"
    assert produk.bahan == "Katun"


def test_ekstrak_teks_mengabaikan_label_yang_tidak_dikenal() -> None:
    produk = ekstrak_teks("keterangan: bukan atribut\nKaos Polos Pria")

    assert produk.nama == "Kaos Polos Pria"


def test_label_nama_eksplisit_menang_atas_baris_pertama() -> None:
    produk = ekstrak_teks("Kaos X\nnama: Kemeja Pria")

    assert produk.nama == "Kemeja Pria"


def test_ekstrak_teks_mendukung_baris_crlf() -> None:
    produk = ekstrak_teks("Kaos\r\nwarna: htm")

    assert produk.nama == "Kaos"
    assert produk.warna == "Hitam"


def test_nilai_merek_mempertahankan_huruf_asli_dan_merapikan_spasi() -> None:
    produk = ekstrak_teks("nama: Kaos\nmerek:  ONEck   Indonesia  ")

    assert produk.merek == "ONEck Indonesia"


def test_fitur_dipisah_dengan_koma_atau_titik_koma() -> None:
    produk = ekstrak_teks("nama: Kaos\nfitur: adem, ; tidak mudah luntur;,")

    assert produk.fitur == ["Adem", "Tidak Mudah Luntur"]


@pytest.mark.parametrize("teks", ["merek: Oneck", ""])
def test_ekstrak_teks_gagal_bila_nama_tidak_ditemukan(teks: str) -> None:
    with pytest.raises(ValueError, match="^Nama produk tidak ditemukan$"):
        ekstrak_teks(teks)
