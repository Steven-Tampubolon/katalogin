import base64
import json
from collections.abc import Callable

import httpx
import pytest
from fastapi.testclient import TestClient

from katalogin.api import create_app
from katalogin.openai_compat import OpenAICompatClient


KUNCI = "kunci-uji-rahasia"
JUDUL_DIHARAPKAN = [
    "Oneck Kaos Polos Pria Katun Combed 30s L",
    "Kaos Polos Pria Oneck Hitam Katun Combed 30s",
    "Oneck Kaos Polos Pria Hitam L Adem",
]


@pytest.fixture
def buat_app_openai(tmp_path):
    def buat(
        penangan: Callable[[httpx.Request], httpx.Response],
    ) -> tuple[TestClient, list[httpx.Request]]:
        permintaan: list[httpx.Request] = []

        def penangkap(request: httpx.Request) -> httpx.Response:
            permintaan.append(request)
            return penangan(request)

        klien = OpenAICompatClient(
            "kunci-uji-rahasia",
            "model-uji",
            "https://integrate.api.nvidia.com/v1",
            transport=httpx.MockTransport(penangkap),
            tidur=lambda detik: None,
        )
        app = create_app(
            db_path=str(tmp_path / "t.db"),
            admin_token="token-uji",
            llm_client=klien,
        )
        return TestClient(app), permintaan

    return buat


def _penangan_sukses(json_kaos: str) -> Callable[[httpx.Request], httpx.Response]:
    def penangan(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": json_kaos}}]},
        )

    return penangan


def _muatan_foto(gambar: bytes) -> dict[str, str]:
    return {
        "platform": "shopee",
        "gambar_base64": base64.b64encode(gambar).decode("ascii"),
    }


def test_generate_foto_openai_compat_mengirim_gambar_dan_menghasilkan_judul(
    buat_app_openai, json_kaos, gambar_png
) -> None:
    klien, permintaan = buat_app_openai(_penangan_sukses(json_kaos))

    respons = klien.post(
        "/generate/foto",
        headers={"X-User-Id": "andi"},
        json=_muatan_foto(gambar_png),
    )

    assert respons.status_code == 200
    data = respons.json()
    assert data["ekstraksi"] == "foto"
    assert data["hasil"]["judul"] == JUDUL_DIHARAPKAN
    assert data["sisa_kredit"] == 4
    assert len(permintaan) == 1
    request = permintaan[0]
    assert str(request.url) == (
        "https://integrate.api.nvidia.com/v1/chat/completions"
    )
    isi = json.loads(request.content)
    content = isi["messages"][0]["content"]
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_generate_teks_openai_compat_menggunakan_ekstraksi_ai(
    buat_app_openai, json_kaos
) -> None:
    klien, _ = buat_app_openai(_penangan_sukses(json_kaos))

    respons = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={
            "platform": "shopee",
            "teks": "kaos oneck hitam",
            "gunakan_ai": True,
        },
    )

    assert respons.status_code == 200
    data = respons.json()
    assert data["ekstraksi"] == "ai"
    assert data["hasil"]["judul"] == JUDUL_DIHARAPKAN


def test_generate_foto_openai_compat_mengulang_429_tiga_kali(
    buat_app_openai, gambar_png
) -> None:
    jumlah = 0

    def penangan(_request: httpx.Request) -> httpx.Response:
        nonlocal jumlah
        jumlah += 1
        return httpx.Response(429, json={"error": "kuota"})

    klien, _ = buat_app_openai(penangan)

    respons = klien.post(
        "/generate/foto",
        headers={"X-User-Id": "andi"},
        json=_muatan_foto(gambar_png),
    )

    assert respons.status_code == 502
    assert respons.json() == {
        "detail": (
            "Layanan AI gagal: Kuota atau batas laju AI terlampaui (HTTP 429)"
        )
    }
    assert jumlah == 3
    kredit = klien.get("/kredit", headers={"X-User-Id": "andi"})
    assert kredit.json()["kredit"] == 5


def test_generate_foto_openai_compat_tidak_mengubah_kredit_untuk_json_ruak(
    buat_app_openai, gambar_png
) -> None:
    def penangan(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "bukan json"}}]},
        )

    klien, _ = buat_app_openai(penangan)

    respons = klien.post(
        "/generate/foto",
        headers={"X-User-Id": "andi"},
        json=_muatan_foto(gambar_png),
    )

    assert respons.status_code == 422
    assert respons.json() == {"detail": "Gagal membaca produk dari gambar"}
    kredit = klien.get("/kredit", headers={"X-User-Id": "andi"})
    assert kredit.json()["kredit"] == 5


def test_generate_foto_openai_compat_tidak_memanggil_llm_saat_kredit_habis(
    buat_app_openai, produk_kaos, gambar_png
) -> None:
    jumlah = 0

    def penangan(_request: httpx.Request) -> httpx.Response:
        nonlocal jumlah
        jumlah += 1
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

    klien, _ = buat_app_openai(penangan)

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
    assert jumlah == 0


def test_api_openai_compat_tidak_membocorkan_kunci_api(
    buat_app_openai, json_kaos, gambar_png
) -> None:
    klien, _ = buat_app_openai(_penangan_sukses(json_kaos))

    respons = [
        klien.post(
            "/generate/foto",
            headers={"X-User-Id": "andi"},
            json=_muatan_foto(gambar_png),
        ),
        klien.post(
            "/generate",
            headers={"X-User-Id": "budi"},
            json={
                "platform": "shopee",
                "teks": "kaos oneck hitam",
                "gunakan_ai": True,
            },
        ),
        klien.get("/kredit", headers={"X-User-Id": "budi"}),
    ]

    for hasil in respons:
        assert KUNCI not in hasil.text
