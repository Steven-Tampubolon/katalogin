from katalogin.config import ambil_platform, ambil_tone
from katalogin.models import Product
from katalogin.textutil import potong_kata


_HOOK = {
    "kasual": "Halo kak! Kenalin {label}.",
    "profesional": "{label}. Berikut spesifikasi produk.",
    "singkat": "{label}.",
}

_CTA = {
    "kasual": "Yuk, order sekarang, kak!",
    "profesional": "Silakan lakukan pemesanan atau hubungi kami untuk informasi lebih lanjut.",
    "singkat": "Order sekarang.",
}


def _nilai(nilai: str | None) -> str:
    return nilai.strip() if nilai is not None else ""


def _spesifikasi(produk: Product) -> str:
    baris: list[str] = []
    for judul, nilai in (
        ("Bahan", produk.bahan),
        ("Ukuran", produk.ukuran),
        ("Warna", produk.warna),
        ("Fungsi", produk.fungsi),
    ):
        isi = _nilai(nilai)
        if isi:
            baris.append(f"- {judul}: {isi}")

    fitur = [isi for nilai in produk.fitur if (isi := _nilai(nilai))]
    if fitur:
        baris.append(f"- Fitur: {', '.join(fitur)}")

    if not baris:
        return ""
    return "\n".join(["Spesifikasi:", *baris])


def buat_deskripsi(produk: Product, platform: str, tone: str) -> str:
    konfigurasi = ambil_platform(platform)
    nada = ambil_tone(tone)

    merek = _nilai(produk.merek)
    nama = _nilai(produk.nama)
    label = f"{merek} {nama}" if merek else nama

    bagian = [_HOOK[nada].format(label=label)]
    spesifikasi = _spesifikasi(produk)
    if spesifikasi:
        bagian.append(spesifikasi)
    bagian.append(_CTA[nada])

    deskripsi = "\n\n".join(bagian)
    return potong_kata(deskripsi, int(konfigurasi["deskripsi_maks"]))
