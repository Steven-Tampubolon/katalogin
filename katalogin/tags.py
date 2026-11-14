import re

from katalogin.config import ambil_platform
from katalogin.models import Product
from katalogin.textutil import rapikan_spasi


def _teks(nilai: str | None) -> str:
    if nilai is None:
        return ""
    return rapikan_spasi(nilai).lower()


def _gabung(*bagian: str) -> str:
    return " ".join(nilai for nilai in bagian if nilai)


def buat_tags(produk: Product, platform: str) -> list[str]:
    konfigurasi = ambil_platform(platform)
    nama = _teks(produk.nama)
    merek = _teks(produk.merek)
    warna = _teks(produk.warna)
    bahan = _teks(produk.bahan)
    fungsi = _teks(produk.fungsi)
    kandidat = [
        _gabung(nama),
        _gabung(merek, nama),
        _gabung(nama, warna),
        _gabung(nama, bahan),
        _gabung(nama, fungsi),
    ]
    kandidat.extend(_teks(fitur) for fitur in produk.fitur)

    hashtag = bool(konfigurasi["hashtag"])
    tag_maks = int(konfigurasi["tag_maks"])
    hasil: list[str] = []
    terlihat: set[str] = set()
    for nilai in kandidat:
        if not nilai:
            continue
        tag = f"#{re.sub(r'[^0-9a-z]', '', nilai)}" if hashtag else nilai
        kunci = tag.casefold()
        if kunci in terlihat:
            continue
        terlihat.add(kunci)
        hasil.append(tag)
        if len(hasil) == tag_maks:
            break
    return hasil
