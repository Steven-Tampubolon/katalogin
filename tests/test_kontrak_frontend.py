import json
import os
from typing import Any

import pytest
from fastapi.testclient import TestClient
from katalogin.api import create_app


def _shape_jenis(value: Any) -> Any:
    """Compare structure: keys only, ignoring actual string values."""
    if isinstance(value, dict):
        return {k: _shape_jenis(v) for k, v in value.items()}
    if isinstance(value, list):
        if len(value) == 0:
            return []
        return [_shape_jenis(value[0])]
    return None  # placeholder for non-dict/non-list values


def _load_contoh() -> dict[str, Any]:
    path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "frontend",
        "src",
        "contoh-respons.json",
    )
    with open(path) as f:
        return json.load(f)


def _cek_bentuk(aktual: dict[str, Any], contoh: dict[str, Any]) -> None:
    actual_shape = _shape_jenis(aktual)
    expected_shape = _shape_jenis(contoh)
    assert actual_shape == expected_shape, (
        f"Bentuk berbeda:\n  Aktual:   {json.dumps(actual_shape, indent=2)}\n  Expected: {json.dumps(expected_shape, indent=2)}"
    )


@pytest.fixture
def klien(tmp_path) -> TestClient:
    return TestClient(
        create_app(db_path=str(tmp_path / "t.db"), admin_token="token-uji")
    )


def test_kontrak_frontend_shape(klien: TestClient) -> None:
    resp = klien.post(
        "/generate",
        json={
            "platform": "shopee",
            "tone": "kasual",
            "produk": {
                "nama": "Kaos Polos Pria",
                "bahan": "katun combed 30s",
            },
            "teks": None,
            "gunakan_ai": False,
        },
        headers={"X-User-Id": "u1"},
    )
    assert resp.status_code == 200
    data = resp.json()
    contoh = _load_contoh()
    _cek_bentuk(data, contoh)