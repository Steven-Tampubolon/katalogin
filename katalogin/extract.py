import re

from katalogin.models import Product
from katalogin.textutil import rapikan_spasi, rapikan_teks

_SINGKATAN = {
    "ktn": "katun",
    "pjg": "panjang",
    "lgn": "lengan",
    "pdk": "pendek",
    "htm": "hitam",
    "pth": "putih",
    "mrh": "merah",
    "bhn": "bahan",
}

_LABEL = {
    "nama": "nama",
    "produk": "nama",
    "barang": "nama",
    "nm": "nama",
    "merek": "merek",
    "brand": "merek",
    "bahan": "bahan",
    "bhn": "bahan",
    "material": "bahan",
    "ukuran": "ukuran",
    "uk": "ukuran",
    "size": "ukuran",
    "warna": "warna",
    "wrn": "warna",
    "color": "warna",
    "fungsi": "fungsi",
    "kegunaan": "fungsi",
    "fitur": "fitur",
    "keunggulan": "fitur",
}

_POLAT_LABEL = re.compile(r"^\s*([A-Za-z]+)\s*[:=]\s*(.+?)\s*$")


def perluas_singkatan(teks: str) -> str:
    hasil = teks
    for singkatan, kata_penuh in _SINGKATAN.items():
        hasil = re.sub(
            rf"\b{singkatan}\b", kata_penuh, hasil, flags=re.IGNORECASE
        )
    return hasil


def _rapikan_nilai(teks: str) -> str:
    return rapikan_teks(perluas_singkatan(teks))


def ekstrak_teks(teks: str) -> Product:
    nama: str | None = None
    merek: str | None = None
    bahan: str | None = None
    ukuran: str | None = None
    warna: str | None = None
    fungsi: str | None = None
    fitur: list[str] = []
    nama_eksplisit = False
    nama_calon: str | None = None

    for baris in teks.splitlines():
        cocok = _POLAT_LABEL.match(baris)
        if cocok is not None:
            label = cocok.group(1).lower()
            if label not in _LABEL:
                continue

            nilai = cocok.group(2)
            atribut = _LABEL[label]
            if atribut == "merek":
                merek = rapikan_spasi(nilai)
            elif atribut == "fitur":
                fitur.extend(
                    _rapikan_nilai(item)
                    for item in re.split(r"[,;]", nilai)
                    if item.strip()
                )
            else:
                nilai_rapih = _rapikan_nilai(nilai)
                if atribut == "nama":
                    nama = nilai_rapih
                    nama_eksplisit = True
                elif atribut == "bahan":
                    bahan = nilai_rapih
                elif atribut == "ukuran":
                    ukuran = nilai_rapih
                elif atribut == "warna":
                    warna = nilai_rapih
                elif atribut == "fungsi":
                    fungsi = nilai_rapih
        elif baris.strip() and nama_calon is None:
            nama_calon = baris

    if not nama_eksplisit and nama_calon is not None:
        nama = _rapikan_nilai(nama_calon)

    if not nama:
        raise ValueError("Nama produk tidak ditemukan")

    return Product(
        nama=nama,
        merek=merek,
        bahan=bahan,
        ukuran=ukuran,
        warna=warna,
        fungsi=fungsi,
        fitur=fitur,
    )
