from katalogin.config import ambil_platform
from katalogin.models import Product
from katalogin.textutil import potong_kata, rapikan_spasi


def _gabung(*bagian: str | None) -> str:
    return " ".join(
        nilai.strip() for nilai in bagian if nilai is not None and nilai.strip()
    )


def buat_judul(produk: Product, platform: str) -> list[str]:
    konfigurasi = ambil_platform(platform)
    judul_maks = int(konfigurasi["judul_maks"])
    fitur_pertama = produk.fitur[0] if produk.fitur else None
    rumus = [
        (produk.merek, produk.nama, produk.bahan, produk.ukuran),
        (produk.nama, produk.merek, produk.warna, produk.bahan),
        (produk.merek, produk.nama, produk.warna, produk.ukuran, fitur_pertama),
    ]

    hasil: list[str] = []
    terlihat: set[str] = set()
    for bagian in rumus:
        judul = potong_kata(rapikan_spasi(_gabung(*bagian)), judul_maks)
        if not judul or judul.casefold() in terlihat:
            continue
        terlihat.add(judul.casefold())
        hasil.append(judul)
    return hasil
