from pathlib import Path

import httpx

from katalogin.llm import FakeLLM
from katalogin.openai_compat import OpenAICompatClient
from katalogin.uji_llm import main


AKAR_PROYEK = Path(__file__).resolve().parents[1]


def test_main_menangkap_value_error_dari_pembuat_klien(capsys) -> None:
    def buat_klien_gagal(env) -> None:
        raise ValueError("KATALOGIN_LLM_MODEL wajib diisi untuk provider openai")

    kode = main([], env={}, buat_klien=buat_klien_gagal)

    tangkap = capsys.readouterr()
    assert kode == 1
    assert tangkap.out == ""
    assert (
        tangkap.err
        == "GALAT: KATALOGIN_LLM_MODEL wajib diisi untuk provider openai\n"
    )


def test_main_tanpa_klien_openai_menampilkan_galat_kunci(capsys) -> None:
    kode = main(
        [],
        env={"KATALOGIN_LLM_PROVIDER": " OpenAI "},
        buat_klien=lambda env: None,
    )

    tangkap = capsys.readouterr()
    assert kode == 1
    assert tangkap.out == ""
    assert tangkap.err == "GALAT: KATALOGIN_LLM_API_KEY belum diisi\n"


def test_main_tanpa_klien_membaca_provider_dari_lingkungan_sistem(
    capsys, monkeypatch
) -> None:
    monkeypatch.setenv("KATALOGIN_LLM_PROVIDER", "openai")

    kode = main([], env={}, buat_klien=lambda env: None)

    tangkap = capsys.readouterr()
    assert kode == 1
    assert tangkap.out == ""
    assert tangkap.err == "GALAT: KATALOGIN_LLM_API_KEY belum diisi\n"


def test_main_mencetak_klien_dan_balasan_tanpa_kunci(capsys) -> None:
    kunci = "kunci-uji-rahasia"
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Halo"}}]},
        )
    )
    klien = OpenAICompatClient(kunci, "model-uji", transport=transport)

    kode = main([], env={}, buat_klien=lambda env: klien)

    tangkap = capsys.readouterr()
    assert kode == 0
    assert tangkap.err == ""
    assert tangkap.out == (
        "Klien: OpenAICompatClient (model: model-uji)\nBalasan AI: Halo\n"
    )
    assert kunci not in tangkap.out
    assert kunci not in tangkap.err


def test_main_mencetak_klient_fake_tanpa_model(capsys) -> None:
    kode = main([], env={}, buat_klien=lambda env: FakeLLM("Halo"))

    tangkap = capsys.readouterr()
    assert kode == 0
    assert tangkap.err == ""
    assert tangkap.out == "Klien: FakeLLM (model: -)\nBalasan AI: Halo\n"


def test_readme_mendokumentasikan_konfigurasi_provider() -> None:
    readme = (AKAR_PROYEK / "README.md").read_text(encoding="utf-8")

    assert "KATALOGIN_LLM_PROVIDER" in readme
    assert "KATALOGIN_LLM_API_KEY" in readme
    assert "KATALOGIN_LLM_BASE_URL" in readme
    assert "https://integrate.api.nvidia.com/v1" in readme
    assert "https://openrouter.ai/api/v1" in readme
    assert ".env" in readme
