import pytest

from katalogin import db
from katalogin.api import create_app
from katalogin.credits import kurangi, pastikan_pengguna, saldo_efektif
from katalogin.gemini import GeminiClient
from katalogin.llm import FakeLLM
from katalogin.llm_config import buat_klien_dari_env


KUNCI = "kunci-uji-rahasia"


@pytest.mark.parametrize("env", [{}, {"GEMINI_API_KEY": "   "}])
def test_konfigurasi_tanpa_kunci_valid_tidak_membuat_klien(env) -> None:
    assert buat_klien_dari_env(env) is None


def test_konfigurasi_membuat_klien_gemini_dengan_model_bawaan() -> None:
    client = buat_klien_dari_env({"GEMINI_API_KEY": f"  {KUNCI}  "})

    assert isinstance(client, GeminiClient)
    assert client.model == "gemini-3.6-flash"
    assert client._api_key == KUNCI


def test_konfigurasi_menggunakan_model_dari_lingkungan() -> None:
    client = buat_klien_dari_env(
        {
            "GEMINI_API_KEY": KUNCI,
            "KATALOGIN_LLM_MODEL": " gemini-x ",
        }
    )

    assert isinstance(client, GeminiClient)
    assert client.model == "gemini-x"


def test_konfigurasi_membaca_lingkungan_sistem_otomatis(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", KUNCI)

    client = buat_klien_dari_env()

    assert isinstance(client, GeminiClient)


def test_aplikasi_membuat_klien_gemini_dari_lingkungan(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", KUNCI)

    app = create_app(db_path=str(tmp_path / "t.db"))

    assert isinstance(app.state.llm_client, GeminiClient)


def test_aplikasi_tanpa_kunci_tidak_membuat_klien(tmp_path) -> None:
    app = create_app(db_path=str(tmp_path / "t.db"))

    assert app.state.llm_client is None


def test_aplikasi_memakai_klien_yang_disuntikkan(tmp_path) -> None:
    llm = FakeLLM("x")

    app = create_app(db_path=str(tmp_path / "t.db"), llm_client=llm)

    assert app.state.llm_client is llm


def test_fixture_klien_ai_menyuntikkan_klien_yang_sama(buat_klien_ai) -> None:
    llm = FakeLLM("x")

    client = buat_klien_ai(llm)

    assert client.app.state.llm_client is llm


def test_saldo_efektif_memberikan_kredit_gratis_untuk_pengguna_baru(tmp_path) -> None:
    db_path = str(tmp_path / "t.db")
    db.init_db(db_path)
    conn = db.buka(db_path)
    try:
        assert saldo_efektif(conn, "andi") == 5
    finally:
        conn.close()


def test_saldo_efektif_mengikuti_saldo_pengguna_terdaftar(tmp_path) -> None:
    db_path = str(tmp_path / "t.db")
    db.init_db(db_path)
    conn = db.buka(db_path)
    try:
        pastikan_pengguna(conn, "andi", "2026-11-15T10:30:00+00:00")
        kurangi(conn, "andi", 5, "generate", "2026-11-15T10:30:00+00:00")

        assert saldo_efektif(conn, "andi") == 0
    finally:
        conn.close()
