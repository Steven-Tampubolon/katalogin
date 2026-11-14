import pytest

from katalogin.validator import KATA_TERLARANG, bersihkan, cari_pelanggaran, cek_panjang


def test_daftar_kata_terlarang_tepat() -> None:
    assert KATA_TERLARANG == (
        "termurah",
        "paling murah",
        "nomor 1",
        "no 1",
        "no.1",
        "terbaik",
        "terlaris",
        "paling laris",
        "ampuh",
        "100% ampuh",
        "menyembuhkan",
        "pasti sembuh",
        "dijamin sembuh",
        "anti kanker",
        "obat kuat",
    )


def test_cari_pelanggaran_mengabaikan_huruf_besar_kecil() -> None:
    assert cari_pelanggaran("Kaos TERMURAH nomor 1, dijamin sembuh dan termurah") == [
        "termurah",
        "nomor 1",
        "dijamin sembuh",
    ]


@pytest.mark.parametrize(
    "teks",
    [
        "terbaikku",
        "termurah1",
        "1termurah",
        "_termurah",
        "termurah_",
        "Kaos Oneck",
    ],
)
def test_cari_pelanggaran_hanya_mencocokkan_kata_utuh(teks: str) -> None:
    assert cari_pelanggaran(teks) == []


def test_cari_pelanggaran_memprioritaskan_frasa_terpanjang() -> None:
    assert cari_pelanggaran("Ini 100% ampuh") == ["100% ampuh"]


def test_cari_pelanggaran_mengembalikan_frasa_unik_dalam_urutan_pertama() -> None:
    assert cari_pelanggaran("Termurah, termurah, TERLARIS") == ["termurah", "terlaris"]


@pytest.mark.parametrize(
    ("masuk", "harapan"),
    [
        ("Kaos TERMURAH nomor 1 di Indonesia", "Kaos di Indonesia"),
        ("Kaos termurah!", "Kaos!"),
        ("Produk No.1 di kelasnya", "Produk di kelasnya"),
        ("Baris satu termurah\nBaris dua", "Baris satu\nBaris dua"),
        ("Kaos\t\tpolos  pria", "Kaos polos pria"),
        ("Kaos , polos .Hem", "Kaos, polos.Hem"),
        ("Kaos  \nPolos\t", "Kaos\nPolos"),
    ],
)
def test_bersihkan(masuk: str, harapan: str) -> None:
    assert bersihkan(masuk) == harapan


def test_cek_panjang_menerima_batas_tepat() -> None:
    assert cek_panjang("abc", 3) is True


def test_cek_panjang_menolak_teks_lebih_panjang() -> None:
    assert cek_panjang("abcd", 3) is False
