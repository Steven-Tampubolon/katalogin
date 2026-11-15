import pytest
from fastapi.testclient import TestClient

from katalogin.api import create_app
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
