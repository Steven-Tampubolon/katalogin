import pytest

from katalogin.textutil import potong_kata, rapikan_spasi, rapikan_teks


@pytest.mark.parametrize(
    ("masuk", "harapan"),
    [
        ("a   b \n c", "a b c"),
        ("\t a\nb \r\n", "a b"),
    ],
)
def test_rapikan_spasi(masuk: str, harapan: str) -> None:
    assert rapikan_spasi(masuk) == harapan


@pytest.mark.parametrize(
    ("masuk", "harapan"),
    [
        ("  KAOS   polos pria ", "Kaos Polos Pria"),
        ("ukuran xl", "Ukuran XL"),
        ("tas pu leather", "Tas PU Leather"),
        ("katun combed 30s", "Katun Combed 30s"),
        ("t-shirt", "T-shirt"),
        ("usb led l 2x", "USB LED L 2x"),
        ("", ""),
        (" \t\n", ""),
    ],
)
def test_rapikan_teks(masuk: str, harapan: str) -> None:
    assert rapikan_teks(masuk) == harapan


@pytest.mark.parametrize(
    ("masuk", "maks", "harapan"),
    [
        ("satu dua tiga empat", 12, "satu dua"),
        ("abc", 10, "abc"),
        ("satu dua", 8, "satu dua"),
        ("satu dua tiga", 9, "satu dua"),
        ("satu dua tiga", 8, "satu dua"),
        ("satu, dua tiga", 6, "satu"),
        ("abcdefghij", 5, "abcde"),
        ("abc", 0, ""),
        ("abc", -1, ""),
        ("satu; dua", 6, "satu"),
        ("satu: dua", 6, "satu"),
        ("satu- dua", 6, "satu"),
        ("satu/ dua", 6, "satu"),
    ],
)
def test_potong_kata(masuk: str, maks: int, harapan: str) -> None:
    assert potong_kata(masuk, maks) == harapan
