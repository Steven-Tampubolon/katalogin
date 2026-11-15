import pytest

from katalogin.llm import (
    PROMPT_FOTO,
    FakeLLM,
    LLMClient,
    LLMError,
    coba_ekstrak_dengan_llm,
    ekstrak_dari_gambar,
)


class KlienTeks(LLMClient):
    def complete(self, prompt: str) -> str:
        return "{}"


def test_prompt_foto_meminta_json_dan_satu_kunci() -> None:
    assert "JSON" in PROMPT_FOTO
    assert "null" in PROMPT_FOTO
    for kunci in ("nama", "merek", "bahan", "ukuran", "warna", "fungsi", "fitur"):
        assert kunci in PROMPT_FOTO


def test_ekstrak_dari_gambar_menghasilkan_produk_dan_mencatat_gambar(
    kaos, gambar_png: bytes, json_kaos: str
) -> None:
    client = FakeLLM(json_kaos)

    produk = ekstrak_dari_gambar(gambar_png, "image/png", client)

    assert produk == kaos
    assert client.gambar == [(PROMPT_FOTO, gambar_png, "image/png")]


def test_ekstrak_dari_gambar_menerima_json_dalam_pagar_markdown(
    kaos, gambar_png: bytes, json_kaos: str
) -> None:
    client = FakeLLM(f"```json\n{json_kaos}\n```")

    assert ekstrak_dari_gambar(gambar_png, "image/png", client) == kaos


@pytest.mark.parametrize("respons", ["bukan json", '{"nama":""}'])
def test_ekstrak_dari_gambar_melempar_value_error_untuk_json_tidak_valid(
    gambar_png: bytes, respons: str
) -> None:
    client = FakeLLM(respons)

    with pytest.raises(ValueError, match="^Gagal membaca produk dari gambar$"):
        ekstrak_dari_gambar(gambar_png, "image/png", client)


def test_ekstrak_dari_gambar_membiarkan_llm_error_naik(
    gambar_png: bytes
) -> None:
    client = FakeLLM(LLMError("kuota"))

    with pytest.raises(LLMError, match="^kuota$"):
        ekstrak_dari_gambar(gambar_png, "image/png", client)


def test_ekstrak_dari_gambar_membiarkan_galat_klien_naik(
    gambar_png: bytes
) -> None:
    client = FakeLLM(RuntimeError("x"))

    with pytest.raises(RuntimeError, match="^x$"):
        ekstrak_dari_gambar(gambar_png, "image/png", client)


def test_llm_client_tanpa_gambar_melempar_not_implemented(gambar_png: bytes) -> None:
    client = KlienTeks()

    with pytest.raises(
        NotImplementedError, match="^Klien ini tidak mendukung gambar$"
    ):
        client.complete_dengan_gambar(PROMPT_FOTO, gambar_png, "image/png")


def test_coba_ekstrak_dengan_llm_mengembalikan_none_untuk_json_tidak_valid() -> None:
    assert coba_ekstrak_dengan_llm("x", FakeLLM("bukan json")) is None


def test_coba_ekstrak_dengan_llm_mengembalikan_none_bila_klien_gagal() -> None:
    assert coba_ekstrak_dengan_llm("x", FakeLLM(RuntimeError("x"))) is None


def test_coba_ekstrak_dengan_llm_menghasilkan_produk_dari_json(
    kaos, json_kaos: str
) -> None:
    assert coba_ekstrak_dengan_llm("x", FakeLLM(json_kaos)) == kaos
