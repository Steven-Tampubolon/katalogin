import base64
import dataclasses

import pytest

from katalogin.llm import FakeLLM, LLMClient, LLMError


JUDUL_DIHARAPKAN = [
    "Oneck Kaos Polos Pria Katun Combed 30s L",
    "Kaos Polos Pria Oneck Hitam Katun Combed 30s",
    "Oneck Kaos Polos Pria Hitam L Adem",
]


class KlienTeks(LLMClient):
    def complete(self, prompt: str) -> str:
        return "{}"


def _base64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _muatan_foto(data: bytes) -> dict[str, str]:
    return {"platform": "shopee", "gambar_base64": _base64(data)}


def test_generate_foto_menghasilkan_konten_dan_menyimpan_riwayat(
    buat_klien_ai, json_kaos, kaos, gambar_png
) -> None:
    llm = FakeLLM(json_kaos)
    klien = buat_klien_ai(llm)

    respons = klien.post(
        "/generate/foto",
        headers={"X-User-Id": "andi"},
        json=_muatan_foto(gambar_png),
    )

    assert respons.status_code == 200
    data = respons.json()
    assert data["hasil"]["judul"] == JUDUL_DIHARAPKAN
    assert data["sisa_kredit"] == 4
    assert data["ekstraksi"] == "foto"
    assert data["produk_terbaca"] == dataclasses.asdict(kaos)
    assert llm.gambar[0][1] == gambar_png
    assert llm.gambar[0][2] == "image/png"
    assert klien.get(
        "/riwayat", headers={"X-User-Id": "andi"}
    ).json()["total"] == 1


@pytest.mark.parametrize(
    ("nama_fixture", "mime"),
    [
        ("gambar_jpeg", "image/jpeg"),
        ("gambar_webp", "image/webp"),
    ],
)
def test_generate_foto_mengenali_mime_jpeg_dan_webp(
    buat_klien_ai, json_kaos, request, nama_fixture, mime
) -> None:
    llm = FakeLLM(json_kaos)
    klien = buat_klien_ai(llm)
    gambar = request.getfixturevalue(nama_fixture)

    respons = klien.post(
        "/generate/foto",
        headers={"X-User-Id": "andi"},
        json=_muatan_foto(gambar),
    )

    assert respons.status_code == 200
    assert llm.gambar[0][1] == gambar
    assert llm.gambar[0][2] == mime


def test_generate_foto_tanpa_klien_mengembalikan_503(klien) -> None:
    respons = klien.post(
        "/generate/foto",
        headers={"X-User-Id": "andi"},
        json=_muatan_foto(b"\x89PNG\r\n\x1a\n"),
    )

    assert respons.status_code == 503
    assert respons.json() == {"detail": "Layanan AI belum dikonfigurasi"}
    assert klien.get(
        "/kredit", headers={"X-User-Id": "andi"}
    ).json()["kredit"] == 5


def test_generate_foto_memeriksa_konfigurasi_ai_sebelum_gambar(klien) -> None:
    respons = klien.post(
        "/generate/foto",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "gambar_base64": "bukan base64!!"},
    )

    assert respons.status_code == 503
    assert respons.json() == {"detail": "Layanan AI belum dikonfigurasi"}


def test_generate_foto_menolak_gambar_bukan_base64(buat_klien_ai) -> None:
    llm = FakeLLM("{}")
    klien = buat_klien_ai(llm)

    respons = klien.post(
        "/generate/foto",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "gambar_base64": "bukan base64!!"},
    )

    assert respons.status_code == 400
    assert respons.json() == {"detail": "Gambar bukan base64 yang valid"}
    assert llm.gambar == []


def test_generate_foto_menolak_format_gambar_tidak_didukung(buat_klien_ai) -> None:
    llm = FakeLLM("{}")
    klien = buat_klien_ai(llm)

    respons = klien.post(
        "/generate/foto",
        headers={"X-User-Id": "andi"},
        json=_muatan_foto(b"GIF89a"),
    )

    assert respons.status_code == 400
    assert respons.json() == {
        "detail": "Format gambar tidak didukung (JPEG, PNG, atau WebP)"
    }
    assert llm.gambar == []


def test_generate_foto_menolak_gambar_lebih_dari_5_mb(buat_klien_ai) -> None:
    llm = FakeLLM("{}")
    klien = buat_klien_ai(llm)
    header_png = b"\x89PNG\r\n\x1a\n"
    gambar = header_png + b"\x00" * (5_000_001 - len(header_png))

    respons = klien.post(
        "/generate/foto",
        headers={"X-User-Id": "andi"},
        json=_muatan_foto(gambar),
    )

    assert respons.status_code == 400
    assert respons.json() == {"detail": "Gambar terlalu besar (maksimum 5 MB)"}
    assert llm.gambar == []


def test_generate_foto_menolak_base64_lebih_dari_6800000_karakter(
    buat_klien_ai,
) -> None:
    llm = FakeLLM("{}")
    klien = buat_klien_ai(llm)

    respons = klien.post(
        "/generate/foto",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "gambar_base64": "A" * 6_800_001},
    )

    assert respons.status_code == 422
    assert llm.gambar == []


def test_generate_foto_menolak_body_lebih_dari_7_juta_byte(buat_klien_ai) -> None:
    llm = FakeLLM("{}")
    klien = buat_klien_ai(llm)

    respons = klien.post(
        "/generate/foto",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "gambar_base64": "A" * 7_000_000},
    )

    assert respons.status_code == 413
    assert respons.json() == {"detail": "Permintaan terlalu besar"}
    assert llm.gambar == []


def test_generate_foto_base64_1_5_juta_karakter_diproses_sebagai_gambar(
    buat_klien_ai,
) -> None:
    llm = FakeLLM("{}")
    klien = buat_klien_ai(llm)

    respons = klien.post(
        "/generate/foto",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "gambar_base64": "A" * 1_500_000},
    )

    assert respons.status_code == 400
    assert respons.json() == {
        "detail": "Format gambar tidak didukung (JPEG, PNG, atau WebP)"
    }
    assert llm.gambar == []


def test_generate_foto_llm_error_mengembalikan_502_dan_tidak_mengubah_kredit(
    buat_klien_ai, gambar_png
) -> None:
    llm = FakeLLM(LLMError("kuota habis"))
    klien = buat_klien_ai(llm)

    respons = klien.post(
        "/generate/foto",
        headers={"X-User-Id": "andi"},
        json=_muatan_foto(gambar_png),
    )

    assert respons.status_code == 502
    assert respons.json() == {"detail": "Layanan AI gagal: kuota habis"}
    assert klien.get(
        "/kredit", headers={"X-User-Id": "andi"}
    ).json()["kredit"] == 5
    assert klien.get(
        "/riwayat", headers={"X-User-Id": "andi"}
    ).json()["total"] == 0


def test_generate_foto_json_tidak_valid_mengembalikan_422_dan_tidak_mengubah_kredit(
    buat_klien_ai, gambar_png
) -> None:
    llm = FakeLLM("bukan json")
    klien = buat_klien_ai(llm)

    respons = klien.post(
        "/generate/foto",
        headers={"X-User-Id": "andi"},
        json=_muatan_foto(gambar_png),
    )

    assert respons.status_code == 422
    assert respons.json() == {"detail": "Gagal membaca produk dari gambar"}
    assert klien.get(
        "/kredit", headers={"X-User-Id": "andi"}
    ).json()["kredit"] == 5
    assert klien.get(
        "/riwayat", headers={"X-User-Id": "andi"}
    ).json()["total"] == 0


def test_generate_foto_klien_tanpa_dukungan_gambar_mengembalikan_503(
    buat_klien_ai, gambar_png
) -> None:
    klien = buat_klien_ai(KlienTeks())

    respons = klien.post(
        "/generate/foto",
        headers={"X-User-Id": "andi"},
        json=_muatan_foto(gambar_png),
    )

    assert respons.status_code == 503
    assert respons.json() == {"detail": "Layanan AI belum mendukung gambar"}


def test_generate_foto_menolak_kredit_kosong_sebelum_memanggil_llm(
    buat_klien_ai, produk_kaos, gambar_png
) -> None:
    llm = FakeLLM("{}")
    klien = buat_klien_ai(llm)

    for _ in range(5):
        respons = klien.post(
            "/generate",
            headers={"X-User-Id": "andi"},
            json={"platform": "shopee", "produk": produk_kaos},
        )
        assert respons.status_code == 200

    respons = klien.post(
        "/generate/foto",
        headers={"X-User-Id": "andi"},
        json=_muatan_foto(gambar_png),
    )

    assert respons.status_code == 402
    assert respons.json() == {
        "detail": "Kredit tidak cukup: butuh 1, tersisa 0"
    }
    assert llm.gambar == []


def test_generate_foto_mengembalikan_400_bila_platform_tidak_dikenal(
    buat_klien_ai, json_kaos, gambar_png
) -> None:
    llm = FakeLLM(json_kaos)
    klien = buat_klien_ai(llm)
    muatan = _muatan_foto(gambar_png)
    muatan["platform"] = "tidak-dikenal"

    respons = klien.post(
        "/generate/foto",
        headers={"X-User-Id": "andi"},
        json=muatan,
    )

    assert respons.status_code == 400
    assert respons.json()["detail"].startswith("Platform tidak dikenal:")


def test_generate_foto_membutuhkan_x_user_id(buat_klien_ai, gambar_png) -> None:
    klien = buat_klien_ai(FakeLLM("{}"))

    respons = klien.post("/generate/foto", json=_muatan_foto(gambar_png))

    assert respons.status_code == 401


@pytest.mark.parametrize("field", ["platform", "tone"])
def test_generate_foto_menolak_platform_dan_tone_lebih_dari_30_karakter(
    buat_klien_ai, gambar_png, field
) -> None:
    klien = buat_klien_ai(FakeLLM("{}"))
    muatan = _muatan_foto(gambar_png)
    muatan[field] = "A" * 31

    respons = klien.post(
        "/generate/foto",
        headers={"X-User-Id": "andi"},
        json=muatan,
    )

    assert respons.status_code == 422
