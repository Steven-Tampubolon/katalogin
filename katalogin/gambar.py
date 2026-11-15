import base64

BATAS_GAMBAR_BYTE = 5_000_000

_AWALAN_JPEG = b"\xff\xd8\xff"
_AWALAN_PNG = b"\x89PNG\r\n\x1a\n"

PESAN_FORMAT_TIDAK_DIDUKUNG = "Format gambar tidak didukung (JPEG, PNG, atau WebP)"
PESAN_BUKAN_BASE64 = "Gambar bukan base64 yang valid"
PESAN_TERLALU_BESAR = "Gambar terlalu besar (maksimum 5 MB)"


def deteksi_mime(data: bytes) -> str:
    if data.startswith(_AWALAN_JPEG):
        return "image/jpeg"
    if data.startswith(_AWALAN_PNG):
        return "image/png"
    if data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    raise ValueError(PESAN_FORMAT_TIDAK_DIDUKUNG)


def decode_base64(teks: str) -> bytes:
    try:
        data = base64.b64decode(teks, validate=True)
    except (ValueError, TypeError):
        raise ValueError(PESAN_BUKAN_BASE64) from None
    if len(data) > BATAS_GAMBAR_BYTE:
        raise ValueError(PESAN_TERLALU_BESAR)
    return data
