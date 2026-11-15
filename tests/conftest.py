from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from katalogin.api import create_app
from katalogin.llm import LLMClient
from katalogin.models import Product


@pytest.fixture
def kaos() -> Product:
    return Product(
        nama="Kaos Polos Pria",
        merek="Oneck",
        bahan="Katun Combed 30s",
        ukuran="L",
        warna="Hitam",
        fungsi="Harian",
        fitur=["Adem", "Tidak Mudah Luntur"],
    )


@pytest.fixture
def produk_kaos() -> dict:
    return {
        "nama": "Kaos Polos Pria",
        "merek": "Oneck",
        "bahan": "Katun Combed 30s",
        "ukuran": "L",
        "warna": "Hitam",
        "fungsi": "Harian",
        "fitur": ["Adem", "Tidak Mudah Luntur"],
    }


@pytest.fixture
def klien(tmp_path) -> TestClient:
    return TestClient(
        create_app(db_path=str(tmp_path / "t.db"), admin_token="token-uji")
    )


@pytest.fixture
def buat_klien_ai(tmp_path) -> Callable[[LLMClient], TestClient]:
    def buat(llm: LLMClient) -> TestClient:
        return TestClient(
            create_app(
                db_path=str(tmp_path / "t.db"),
                admin_token="token-uji",
                llm_client=llm,
            )
        )

    return buat


@pytest.fixture
def json_kaos() -> str:
    return (
        '{"nama":"kaos polos pria","merek":"Oneck","bahan":"katun combed 30s",'
        '"ukuran":"l","warna":"hitam","fungsi":"harian",'
        '"fitur":["adem","tidak mudah luntur"]}'
    )


@pytest.fixture
def gambar_png() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


@pytest.fixture
def gambar_jpeg() -> bytes:
    return b"\xff\xd8\xff\xe0" + b"\x00" * 32


@pytest.fixture
def gambar_webp() -> bytes:
    return b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 8


@pytest.fixture(autouse=True)
def bersihkan_env_llm(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("KATALOGIN_LLM_MODEL", raising=False)
