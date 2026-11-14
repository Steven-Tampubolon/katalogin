UKURAN_DAN_SINGKATAN: frozenset[str] = frozenset(
    {"XS", "S", "M", "L", "XL", "XXL", "XXXL", "LED", "USB", "PU", "HD",
     "UV", "TWS", "LCD", "SPF", "TV"}
)

KARAKTER_UJUNG: str = " ,;:-/"


def rapikan_spasi(teks: str) -> str:
    """Gabungkan semua spasi, tab, dan baris baru menjadi satu spasi."""
    return " ".join(teks.split())


def rapikan_teks(teks: str) -> str:
    """Rapikan teks per kata: singkatan jadi huruf besar, sisanya capitalize."""
    kata_kata = []
    for kata in teks.split():
        if any(karakter.isdigit() for karakter in kata):
            kata_kata.append(kata)
        elif kata.upper() in UKURAN_DAN_SINGKATAN:
            kata_kata.append(kata.upper())
        else:
            kata_kata.append(kata.capitalize())
    return " ".join(kata_kata)


def potong_kata(teks: str, maks: int) -> str:
    """Potong teks pada batas kata hingga maksimum `maks` karakter."""
    if maks <= 0:
        return ""
    if len(teks) <= maks:
        return teks
    if teks[maks] == " ":
        hasil = teks[:maks]
    else:
        spasi_terakhir = teks.rfind(" ", 0, maks)
        if spasi_terakhir == -1:
            hasil = teks[:maks]
        else:
            hasil = teks[:spasi_terakhir]
    return hasil.rstrip(KARAKTER_UJUNG)
