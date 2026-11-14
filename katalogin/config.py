PLATFORMS: dict[str, dict[str, int | bool]] = {
    "shopee": {
        "judul_maks": 255,
        "deskripsi_maks": 3000,
        "tag_maks": 10,
        "hashtag": False,
    },
    "tokopedia": {
        "judul_maks": 70,
        "deskripsi_maks": 2000,
        "tag_maks": 5,
        "hashtag": False,
    },
    "tiktok": {
        "judul_maks": 255,
        "deskripsi_maks": 5000,
        "tag_maks": 5,
        "hashtag": True,
    },
}

TONES = ("kasual", "profesional", "singkat")


def ambil_platform(nama: str) -> dict[str, int | bool]:
    kunci = nama.strip().lower()
    if kunci not in PLATFORMS:
        raise ValueError(
            f"Platform tidak dikenal: {nama}. Pilihan: shopee, tokopedia, tiktok"
        )
    return PLATFORMS[kunci]


def ambil_tone(nama: str) -> str:
    tone = nama.strip().lower()
    if tone not in TONES:
        raise ValueError(
            f"Tone tidak dikenal: {nama}. Pilihan: kasual, profesional, singkat"
        )
    return tone
