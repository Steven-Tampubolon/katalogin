import pytest

from fastapi.testclient import TestClient

from katalogin.llm import (
    ALASAN_PENYEDIA_GAGAL,
    ALASAN_RESPONS_TIDAK_VALID,
    CATATAN_ALASAN,
    FakeLLM,
    coba_ekstrak_dengan_llm_rinci,
    LLMClient,
    LLMError,
)
from katalogin.models import Product


def test_coba_ekstrak_dengan_llm_rinci_penyedia_gagal_runtimeerror() -> None:
    result = coba_ekstrak_dengan_llm_rinci("x", FakeLLM(RuntimeError("rahasia-xyz")))
    assert result == (None, ALASAN_PENYEDIA_GAGAL)


def test_coba_ekstrak_dengan_llm_rinci_penyedia_gagal_llmerror() -> None:
    result = coba_ekstrak_dengan_llm_rinci("x", FakeLLM(LLMError("kuota")))
    assert result == (None, ALASAN_PENYEDIA_GAGAL)


@pytest.mark.parametrize(
    "respons,expected",
    [
        ("bukan json", (None, ALASAN_RESPONS_TIDAK_VALID)),
        ('{"nama":""}', (None, ALASAN_RESPONS_TIDAK_VALID)),
        ('{"nama":123}', (None, ALASAN_RESPONS_TIDAK_VALID)),
        ('{"nama":"Kaos"}', (Product(nama="Kaos"), None)),
    ],
)
def test_coba_ekstrak_dengan_llm_rinci_respons_validasi(respons: str, expected: tuple) -> None:
    result = coba_ekstrak_dengan_llm_rinci("KAOS POLOS PRIA\nbhn: ktn", FakeLLM(respons))
    assert result == expected


def test_coba_ekstrak_dengan_llm_rinci_tidak_ada_log_sukses(caplog) -> None:
    with caplog.at_level("WARNING", logger="katalogin.llm"):
        result = coba_ekstrak_dengan_llm_rinci("KAOS POLOS PRIA\nbhn: ktn", FakeLLM("{\"nama\":\"Kaos\"}"))
    assert result == (Product(nama="Kaos"), None)
    assert "WARNING" not in caplog.text


def test_api_penyedia_gagal(caplog, tmp_path) -> None:
    from katalogin.api import create_app

    with caplog.at_level("WARNING", logger="katalogin.llm"):
        klien = TestClient(
            create_app(db_path=str(tmp_path / "t.db"), admin_token="t", llm_client=FakeLLM(RuntimeError("rahasia-xyz")))
        )
        respons = klien.post(
            "/generate",
            headers={"X-User-Id": "u1"},
            json={"platform": "shopee", "teks": "KAOS POLOS PRIA\nbhn: ktn", "gunakan_ai": True},
        )

    assert respons.status_code == 200
    data = respons.json()
    assert data["ekstraksi"] == "aturan"
    assert data["alasan_fallback"] == ALASAN_PENYEDIA_GAGAL
    assert data["catatan_ai"] == CATATAN_ALASAN[ALASAN_PENYEDIA_GAGAL]
    assert data["sisa_kredit"] == 4
    assert "rahasia-xyz" not in respons.text


def test_api_respons_tidak_valid(caplog, tmp_path) -> None:
    from katalogin.api import create_app

    klien = TestClient(
        create_app(db_path=str(tmp_path / "t.db"), admin_token="t", llm_client=FakeLLM("bukan json"))
    )
    respons = klien.post(
        "/generate",
        headers={"X-User-Id": "u1"},
        json={"platform": "shopee", "teks": "KAOS POLOS PRIA\nbhn: ktn", "gunakan_ai": True},
    )

    assert respons.status_code == 200
    data = respons.json()
    assert data["alasan_fallback"] == ALASAN_RESPONS_TIDAK_VALID
    assert data["catatan_ai"] == CATATAN_ALASAN[ALASAN_RESPONS_TIDAK_VALID]


def test_api_ekstrak_ai_tidak_ada_kunci_extra(caplog, tmp_path) -> None:
    from katalogin.api import create_app

    klien = TestClient(
        create_app(
            db_path=str(tmp_path / "t.db"),
            admin_token="t",
            llm_client=FakeLLM('{"nama":"Kaos Polos Pria"}'),
        )
    )
    respons = klien.post(
        "/generate",
        headers={"X-User-Id": "u1"},
        json={"platform": "shopee", "teks": "KAOS POLOS PRIA\nbhn: ktn", "gunakan_ai": True},
    )

    assert respons.status_code == 200
    data = respons.json()
    assert data["ekstraksi"] == "ai"
    assert "alasan_fallback" not in data
    assert "catatan_ai" not in data


def test_api_gunakan_ai_false_tidak_ada_kunci_extra(caplog, tmp_path) -> None:
    from katalogin.api import create_app

    klien = TestClient(
        create_app(db_path=str(tmp_path / "t.db"), admin_token="t", llm_client=FakeLLM('{"nama":"Kaos"}'))
    )
    respons = klien.post(
        "/generate",
        headers={"X-User-Id": "u1"},
        json={"platform": "shopee", "teks": "KAOS POLOS PRIA\nbhn: ktn", "gunakan_ai": False},
    )

    assert respons.status_code == 200
    data = respons.json()
    assert "ekstraksi" not in data
    assert "alasan_fallback" not in data
    assert "catatan_ai" not in data