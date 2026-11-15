import json

import httpx
import pytest

from katalogin.gemini import GeminiClient
from katalogin.llm import LLMError


KUNCI = "kunci-uji-rahasia"
URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-3.6-flash:generateContent"
)


@pytest.mark.parametrize("api_key", ["", "  "])
def test_konstruktor_menolak_api_key_kosong(api_key: str) -> None:
    with pytest.raises(ValueError, match="^API key Gemini kosong$"):
        GeminiClient(api_key)


def test_repr_tidak_membocorkan_api_key() -> None:
    client = GeminiClient(KUNCI)

    assert client.model == "gemini-3.6-flash"
    assert repr(client) == "GeminiClient(model=gemini-3.6-flash)"
    assert KUNCI not in repr(client)


def test_complete_mengirim_permintaan_teks_dan_menggabungkan_teks() -> None:
    permintaan: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        permintaan.append(request)
        return httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": "A"}, {"text": "B"}]}}]},
        )

    client = GeminiClient(KUNCI, transport=httpx.MockTransport(handler))

    assert client.complete("halo") == "AB"
    assert len(permintaan) == 1
    request = permintaan[0]
    assert request.method == "POST"
    assert str(request.url) == URL
    assert KUNCI not in str(request.url)
    assert request.headers["x-goog-api-key"] == KUNCI
    assert request.headers["content-type"] == "application/json"
    assert json.loads(request.content) == {"contents": [{"parts": [{"text": "halo"}]}]}


def test_complete_mengulang_503_lalu_berhasil() -> None:
    jumlah: list[int] = []
    tidur: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        jumlah.append(1)
        if len(jumlah) == 1:
            return httpx.Response(503, json={"error": "sibuk"})
        return httpx.Response(
            200, json={"candidates": [{"content": {"parts": [{"text": "hasil"}]}}]}
        )

    client = GeminiClient(
        KUNCI,
        transport=httpx.MockTransport(handler),
        tidur=tidur.append,
    )

    assert client.complete("halo") == "hasil"
    assert len(jumlah) == 2
    assert tidur == [1]


def test_complete_mengulang_429_sampai_kuota_habis() -> None:
    jumlah: list[int] = []
    tidur: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        jumlah.append(1)
        return httpx.Response(429, json={"error": "kuota"})

    client = GeminiClient(
        KUNCI,
        transport=httpx.MockTransport(handler),
        tidur=tidur.append,
    )

    with pytest.raises(LLMError) as galat:
        client.complete("halo")

    assert str(galat.value) == "Kuota atau batas laju AI terlampaui (HTTP 429)"
    assert len(jumlah) == 3
    assert tidur == [1, 2]
    assert KUNCI not in str(galat.value)


def test_complete_mengulang_500_sampai_layanan_habis() -> None:
    jumlah: list[int] = []
    tidur: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        jumlah.append(1)
        return httpx.Response(500, json={"error": "gagal"})

    client = GeminiClient(
        KUNCI,
        transport=httpx.MockTransport(handler),
        tidur=tidur.append,
    )

    with pytest.raises(LLMError) as galat:
        client.complete("halo")

    assert str(galat.value) == "Layanan AI tidak tersedia (HTTP 500)"
    assert len(jumlah) == 3
    assert tidur == [1, 2]
    assert KUNCI not in str(galat.value)


@pytest.mark.parametrize("kode", [400, 403])
def test_complete_tidak_mengulang_galat_permintaan(kode: int) -> None:
    jumlah: list[int] = []
    tidur: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        jumlah.append(1)
        return httpx.Response(kode, json={"error": "ditolak"})

    client = GeminiClient(
        KUNCI,
        transport=httpx.MockTransport(handler),
        tidur=tidur.append,
    )

    with pytest.raises(LLMError) as galat:
        client.complete("halo")

    assert str(galat.value) == f"Permintaan ke AI ditolak (HTTP {kode})"
    assert len(jumlah) == 1
    assert tidur == []
    assert KUNCI not in str(galat.value)


def test_complete_mengubah_timeout_menjadi_llm_error() -> None:
    jumlah: list[int] = []
    tidur: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        jumlah.append(1)
        raise httpx.ReadTimeout("waktu habis")

    client = GeminiClient(
        KUNCI,
        transport=httpx.MockTransport(handler),
        tidur=tidur.append,
    )

    with pytest.raises(LLMError) as galat:
        client.complete("halo")

    assert str(galat.value) == "Waktu tunggu AI habis"
    assert len(jumlah) == 3
    assert tidur == [1, 2]
    assert KUNCI not in str(galat.value)


def test_complete_mengubah_transport_error_menjadi_llm_error() -> None:
    jumlah: list[int] = []
    tidur: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        jumlah.append(1)
        raise httpx.ConnectError("koneksi gagal")

    client = GeminiClient(
        KUNCI,
        transport=httpx.MockTransport(handler),
        tidur=tidur.append,
    )

    with pytest.raises(LLMError) as galat:
        client.complete("halo")

    assert str(galat.value) == "Koneksi ke AI gagal"
    assert len(jumlah) == 3
    assert tidur == [1, 2]
    assert KUNCI not in str(galat.value)


@pytest.mark.parametrize(
    "respons",
    [
        httpx.Response(200, json={"candidates": []}),
        httpx.Response(200, json={"candidates": [{"content": {"parts": []}}]}),
        httpx.Response(200, content=b"bukan json"),
    ],
)
def test_complete_menolak_balasan_kosong_atau_tidak_valid(
    respons: httpx.Response,
) -> None:
    jumlah: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        jumlah.append(1)
        return respons

    client = GeminiClient(KUNCI, transport=httpx.MockTransport(handler))

    with pytest.raises(LLMError) as galat:
        client.complete("halo")

    assert str(galat.value) == "Balasan AI kosong atau tidak valid"
    assert len(jumlah) == 1
    assert KUNCI not in str(galat.value)
