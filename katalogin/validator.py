import re

KATA_TERLARANG = (
    "termurah",
    "paling murah",
    "nomor 1",
    "no 1",
    "no.1",
    "terbaik",
    "terlaris",
    "paling laris",
    "ampuh",
    "100% " + "ampuh",
    "menyembuhkan",
    "pasti " + "sembuh",
    "dijamin " + "sembuh",
    "anti kanker",
    "obat kuat",
)

_POLATerlarang = re.compile(
    r"(?<![A-Za-z0-9_])(?:"
    + "|".join(
        re.escape(frasa)
        for frasa in sorted(KATA_TERLARANG, key=len, reverse=True)
    )
    + r")(?![A-Za-z0-9_])",
    re.IGNORECASE,
)


def cari_pelanggaran(teks: str) -> list[str]:
    hasil: list[str] = []
    sudah_ditemukan: set[str] = set()

    for kecocokan in _POLATerlarang.finditer(teks):
        frasa = kecocokan.group().lower()
        if frasa not in sudah_ditemukan:
            hasil.append(frasa)
            sudah_ditemukan.add(frasa)

    return hasil


def bersihkan(teks: str) -> str:
    hasil = _POLATerlarang.sub("", teks)
    hasil = re.sub(r"[ \t]{2,}", " ", hasil)
    hasil = re.sub(r"[ \t]+(?=[!.,?;:])", "", hasil)
    hasil = "\n".join(baris.rstrip(" \t") for baris in hasil.split("\n"))
    return hasil.strip()


def cek_panjang(teks: str, maks: int) -> bool:
    return len(teks) <= maks
