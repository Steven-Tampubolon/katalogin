import pytest

from katalogin.extract import ekstrak_teks
from katalogin.llm import (
    PROMPT_EKSTRAKSI,
    FakeLLM,
    LLMClient,
    ekstrak_dengan_llm,
)
from katalogin.models import Product


def test_llm_client_adalah_kelas_abstrak() -> None:
    with pytest.raises(TypeError):
        LLMClient()


def test_fake_llm_mencatat_prompt_dan_mengembalikan_respons() -> None:
    client = FakeLLM("hasil")

    assert client.complete("prompt") == "hasil"
    assert client.prompts == ["prompt"]


def test_fake_llm_meneruskan_exception_dan_mencatat_prompt() -> None:
    client = FakeLLM(RuntimeError("gagal"))

    with pytest.raises(RuntimeError, match="^gagal$"):
        client.complete("prompt")

    assert client.prompts == ["prompt"]


def test_prompt_ekstraksi_meminta_json_dan_menyertakan_teks() -> None:
    assert "{TEKS}" in PROMPT_EKSTRAKSI
    assert "JSON" in PROMPT_EKSTRAKSI
    for kunci in ("nama", "merek", "bahan", "ukuran", "warna", "fungsi", "fitur"):
        assert kunci in PROMPT_EKSTRAKSI


def test_ekstrak_dengan_llm_menghasilkan_product_dari_json() -> None:
    client = FakeLLM(
        '{"nama":"kaos polos pria","merek":"Oneck","bahan":"katun combed 30s",'
        '"ukuran":"l","warna":"hitam","fungsi":"harian","fitur":["adem"]}'
    )

    assert ekstrak_dengan_llm("KAOS POLOS PRIA\nbhn: ktn", client) == Product(
        nama="Kaos Polos Pria",
        merek="Oneck",
        bahan="Katun Combed 30s",
        ukuran="L",
        warna="Hitam",
        fungsi="Harian",
        fitur=["Adem"],
    )


def test_ekstrak_dengan_llm_menerima_json_dalam_pagar_markdown() -> None:
    respons = (
        '```json\n{"nama":"Kaos","merek":"Oneck","fitur":["adem"]}\n```'
    )
    client = FakeLLM(respons)

    produk = ekstrak_dengan_llm("Kaos\nmerek: Oneck", client)

    assert produk == Product(nama="Kaos", merek="Oneck", fitur=["Adem"])


def test_ekstrak_dengan_llm_mengubah_nilai_null_dan_fitur_tidak_valid() -> None:
    client = FakeLLM('{"nama":"Kaos","merek":null}')

    produk = ekstrak_dengan_llm("Kaos", client)

    assert produk.merek is None
    assert produk.fitur == []


def test_ekstrak_dengan_llm_mengganti_penanda_dengan_teks_supplier() -> None:
    client = FakeLLM('{"nama":"Kaos"}')

    ekstrak_dengan_llm("Kaos Polos Pria\nbahan: katun", client)

    assert len(client.prompts) == 1
    assert "Kaos Polos Pria\nbahan: katun" in client.prompts[0]
    assert "{TEKS}" not in client.prompts[0]


@pytest.mark.parametrize(
    "respons",
    [
        "bukan json",
        '{"nama":""}',
        '{"nama":123}',
    ],
)
def test_ekstrak_dengan_llm_memakai_cadangan_aturan(respons: str) -> None:
    teks = "KAOS POLOS PRIA\nbhn: ktn"
    client = FakeLLM(respons)

    assert ekstrak_dengan_llm(teks, client) == ekstrak_teks(teks)


def test_ekstrak_dengan_llm_memakai_cadangan_bila_client_gagal() -> None:
    teks = "KAOS POLOS PRIA\nbhn: ktn"
    client = FakeLLM(RuntimeError("x"))

    assert ekstrak_dengan_llm(teks, client) == ekstrak_teks(teks)


def test_ekstrak_dengan_llm_membiarkan_galat_cadangan_naik() -> None:
    client = FakeLLM("bukan json")

    with pytest.raises(ValueError, match="^Nama produk tidak ditemukan$"):
        ekstrak_dengan_llm("merek: Oneck", client)
