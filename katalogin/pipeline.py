from dataclasses import dataclass, replace

from katalogin.config import ambil_platform, ambil_tone
from katalogin.descriptions import buat_deskripsi
from katalogin.models import Product
from katalogin.tags import buat_tags
from katalogin.titles import buat_judul
from katalogin.validator import bersihkan, cari_pelanggaran


@dataclass
class Hasil:
    nama_produk: str
    platform: str
    tone: str
    judul: list[str]
    deskripsi: str
    tags: list[str]
    pelanggaran: list[str]


_FIELD_PRODUK = ("nama", "merek", "bahan", "ukuran", "warna", "fungsi")


def _tambah_pelanggaran(
    nilai: str | None, pelanggaran: list[str], sudah_ditemukan: set[str]
) -> None:
    if nilai is None:
        return
    for item in cari_pelanggaran(nilai):
        if item not in sudah_ditemukan:
            pelanggaran.append(item)
            sudah_ditemukan.add(item)


def _bersihkan_produk(produk: Product) -> tuple[Product, list[str]]:
    pelanggaran: list[str] = []
    sudah_ditemukan: set[str] = set()
    nilai_bersih: dict[str, str] = {}

    for field in _FIELD_PRODUK:
        nilai = getattr(produk, field)
        _tambah_pelanggaran(nilai, pelanggaran, sudah_ditemukan)
        nilai_bersih[field] = bersihkan(nilai) if nilai is not None else ""

    if not nilai_bersih["nama"]:
        raise ValueError("Nama produk kosong setelah pembersihan kata terlarang")

    fitur_bersih: list[str] = []
    for fitur in produk.fitur:
        _tambah_pelanggaran(fitur, pelanggaran, sudah_ditemukan)
        nilai = bersihkan(fitur)
        if nilai:
            fitur_bersih.append(nilai)

    produk_bersih = replace(
        produk,
        nama=nilai_bersih["nama"],
        merek=nilai_bersih["merek"] or None,
        bahan=nilai_bersih["bahan"] or None,
        ukuran=nilai_bersih["ukuran"] or None,
        warna=nilai_bersih["warna"] or None,
        fungsi=nilai_bersih["fungsi"] or None,
        fitur=fitur_bersih,
    )
    return produk_bersih, pelanggaran


def generate(produk: Product, platform: str, tone: str = "kasual") -> Hasil:
    ambil_platform(platform)
    tone_normal = ambil_tone(tone)
    platform_normal = platform.strip().lower()

    if not produk.nama or not produk.nama.strip():
        raise ValueError("Nama produk wajib diisi")

    produk_bersih, pelanggaran = _bersihkan_produk(produk)
    return Hasil(
        nama_produk=produk_bersih.nama,
        platform=platform_normal,
        tone=tone_normal,
        judul=buat_judul(produk_bersih, platform_normal),
        deskripsi=buat_deskripsi(produk_bersih, platform_normal, tone_normal),
        tags=buat_tags(produk_bersih, platform_normal),
        pelanggaran=pelanggaran,
    )


def generate_batch(
    daftar_produk: list[Product], platform: str, tone: str = "kasual"
) -> list[Hasil]:
    ambil_platform(platform)
    tone_normal = ambil_tone(tone)
    platform_normal = platform.strip().lower()
    return [
        generate(produk, platform_normal, tone_normal) for produk in daftar_produk
    ]
