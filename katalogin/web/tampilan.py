from katalogin.config import PLATFORMS, TONES
from katalogin.web.klien_api import ApiError


PLATFORM_OPSI = list(PLATFORMS)
TONE_OPSI = list(TONES)


def hitung_karakter(teks: str, maks: int) -> str:
    return f"{len(teks)}/{maks} karakter"


def tags_ke_teks(tags: list[str]) -> str:
    return ", ".join(tags)


def pesan_galat(galat: ApiError) -> str:
    if galat.status == 401:
        return "ID pengguna belum diisi."
    if galat.status == 402:
        return f"{galat.detail}. Kredit habis; hubungi admin untuk menambah kredit."
    if galat.status == 413:
        return "Berkas atau teks terlalu besar. Perkecil lalu coba lagi."
    return galat.detail


def baris_riwayat(item: list[dict]) -> list[dict]:
    return [
        {
            "ID": entri["id"],
            "Waktu": entri["dibuat"],
            "Platform": entri["platform"],
            "Tone": entri["tone"],
            "Produk": entri["nama_produk"],
        }
        for entri in item
    ]


def baris_hasil_csv(hasil: list[dict]) -> list[dict]:
    baris = []
    for entri in hasil:
        judul = entri["judul"]
        baris.append(
            {
                "Produk": entri["nama_produk"],
                "Judul 1": judul[0] if len(judul) > 0 else "",
                "Judul 2": judul[1] if len(judul) > 1 else "",
                "Judul 3": judul[2] if len(judul) > 2 else "",
                "Tag": tags_ke_teks(entri["tags"]),
                "Peringatan": ", ".join(entri["pelanggaran"]),
            }
        )
    return baris
