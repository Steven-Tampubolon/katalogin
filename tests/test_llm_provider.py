import pytest

from katalogin.api import create_app
from katalogin.gemini import GeminiClient
from katalogin.llm import FakeLLM
from katalogin.llm_config import buat_klien_dari_env
from katalogin.openai_compat import OpenAICompatClient


KUNCI = "kunci-uji-rahasia"


@pytest.mark.parametrize(
    "env",
    [{}, {"KATALOGIN_LLM_PROVIDER": "gemini"}],
)
def test_tanpa_kunci_tidak_membuat_klien(env) -> None:
    assert buat_klien_dari_env(env) is None


def test_provider_gemini_memakai_kunci_gemini_dan_model_bawaan() -> None:
    client = buat_klien_dari_env({"GEMINI_API_KEY": KUNCI})

    assert isinstance(client, GeminiClient)
    assert client.model == "gemini-3.6-flash"
    assert client._api_key == KUNCI


def test_provider_gemini_menggunakan_kunci_llm_sebagai_alternatif() -> None:
    client = buat_klien_dari_env({"KATALOGIN_LLM_API_KEY": KUNCI})

    assert isinstance(client, GeminiClient)
    assert client._api_key == KUNCI


def test_provider_gemini_memprioritaskan_kunci_gemini() -> None:
    client = buat_klien_dari_env(
        {
            "GEMINI_API_KEY": "kunci-gemini",
            "KATALOGIN_LLM_API_KEY": "kunci-llm",
        }
    )

    assert isinstance(client, GeminiClient)
    assert client._api_key == "kunci-gemini"


def test_provider_openai_tanpa_kunci_tidak_membuat_klien() -> None:
    assert buat_klien_dari_env({"KATALOGIN_LLM_PROVIDER": "openai"}) is None


def test_provider_openai_membuat_klien_dengan_alamat_dasar_bawaan() -> None:
    client = buat_klien_dari_env(
        {
            "KATALOGIN_LLM_PROVIDER": " OpenAI ",
            "KATALOGIN_LLM_API_KEY": KUNCI,
            "KATALOGIN_LLM_MODEL": "model-uji",
        }
    )

    assert isinstance(client, OpenAICompatClient)
    assert client.model == "model-uji"
    assert client._base_url == "https://api.openai.com/v1"


def test_provider_openai_menormalkan_alamat_dasar_kustom() -> None:
    client = buat_klien_dari_env(
        {
            "KATALOGIN_LLM_PROVIDER": "openai",
            "KATALOGIN_LLM_API_KEY": KUNCI,
            "KATALOGIN_LLM_MODEL": "model-uji",
            "KATALOGIN_LLM_BASE_URL": " https://integrate.api.nvidia.com/v1/ ",
        }
    )

    assert isinstance(client, OpenAICompatClient)
    assert client._base_url == "https://integrate.api.nvidia.com/v1"


def test_provider_openai_tidak_menggunakan_kunci_gemini() -> None:
    client = buat_klien_dari_env(
        {
            "KATALOGIN_LLM_PROVIDER": "openai",
            "GEMINI_API_KEY": KUNCI,
            "KATALOGIN_LLM_MODEL": "model-uji",
        }
    )

    assert client is None


def test_provider_openai_melewati_kunci_gemini_saja_tanpa_model() -> None:
    client = buat_klien_dari_env(
        {
            "KATALOGIN_LLM_PROVIDER": "openai",
            "GEMINI_API_KEY": KUNCI,
        }
    )

    assert client is None


def test_provider_openai_menuntut_model() -> None:
    with pytest.raises(
        ValueError,
        match=r"^KATALOGIN_LLM_MODEL wajib diisi untuk provider openai$",
    ):
        buat_klien_dari_env(
            {
                "KATALOGIN_LLM_PROVIDER": "openai",
                "KATALOGIN_LLM_API_KEY": KUNCI,
            }
        )


def test_provider_openai_menolak_alamat_dasar_tanpa_skema_http() -> None:
    with pytest.raises(
        ValueError,
        match=r"^KATALOGIN_LLM_BASE_URL harus diawali http:// atau https://$",
    ):
        buat_klien_dari_env(
            {
                "KATALOGIN_LLM_PROVIDER": "openai",
                "KATALOGIN_LLM_API_KEY": KUNCI,
                "KATALOGIN_LLM_MODEL": "model-uji",
                "KATALOGIN_LLM_BASE_URL": "ftp://x",
            }
        )


def test_provider_tidak_dikenal_ditolak_walaupun_tanpa_kunci() -> None:
    with pytest.raises(
        ValueError,
        match=(
            r"^KATALOGIN_LLM_PROVIDER tidak dikenal: claude\. "
            r"Pilihan: gemini, openai$"
        ),
    ):
        buat_klien_dari_env({"KATALOGIN_LLM_PROVIDER": "claude"})


def test_aplikasi_membuat_klien_openai_dari_lingkungan(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("KATALOGIN_LLM_PROVIDER", "openai")
    monkeypatch.setenv("KATALOGIN_LLM_API_KEY", KUNCI)
    monkeypatch.setenv("KATALOGIN_LLM_MODEL", "model-uji")

    app = create_app(db_path=str(tmp_path / "t.db"))

    assert isinstance(app.state.llm_client, OpenAICompatClient)


def test_aplikasi_meloloskan_provider_tidak_dikenal(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("KATALOGIN_LLM_PROVIDER", "claude")

    with pytest.raises(ValueError, match="KATALOGIN_LLM_PROVIDER tidak dikenal"):
        create_app(db_path=str(tmp_path / "t.db"))


def test_aplikasi_memakai_klien_yang_disuntikkan_tanpa_membaca_lingkungan(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("KATALOGIN_LLM_PROVIDER", "claude")
    client = FakeLLM("x")

    app = create_app(db_path=str(tmp_path / "t.db"), llm_client=client)

    assert app.state.llm_client is client
