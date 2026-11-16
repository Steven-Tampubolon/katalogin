import base64
import json

import httpx
import pytest

from katalogin.llm import LLMClient, LLMError, ekstrak_dari_gambar
from katalogin.openai_compat import OpenAICompatClient


KUNCI = "kunci-uji-rahasia"


def test_konstruktor_menolak_api_key_kosong() -> None:
    with pytest.raises(ValueError, match="^API key LLM kosong$"):
        OpenAICompatClient("  ", "model-uji")


def test_konstruktor_menolak_model_kosong() -> None:
    with pytest.raises(ValueError, match="^Nama model LLM kosong$"):
        OpenAICompatClient(KUNCI, "  ")


def test_konstruktor_menolak_base_url_tidak_valid() -> None:
    with pytest.raises(
        ValueError,
        match="^Alamat dasar LLM harus diawali http:// atau https://$",
    ):
        OpenAICompatClient(KUNCI, "model-uji", "ftp://x")


def test_konstruktor_memvalidasi_api_key_sebelum_model_dan_base_url() -> None:
    with pytest.raises(ValueError, match="^API key LLM kosong$"):
        OpenAICompatClient("  ", "  ", "ftp://x")


def test_konstruktor_memvalidasi_model_sebelum_base_url() -> None:
    with pytest.raises(ValueError, match="^Nama model LLM kosong$"):
        OpenAICompatClient(KUNCI, "  ", "ftp://x")


def test_repr_tidak_membocorkan_api_key() -> None:
    client = OpenAICompatClient(
        KUNCI,
        "model-uji",
        "https://integrate.api.nvidia.com/v1",
    )

    assert client.model == "model-uji"
    assert repr(client) == (
        "OpenAICompatClient(model=model-uji, "
        "base_url=https://integrate.api.nvidia.com/v1)"
    )
    assert KUNCI not in repr(client)


def test_openai_compat_client_adalah_subkelas_llm_client() -> None:
    client = OpenAICompatClient(KUNCI, "model-uji")

    assert isinstance(client, LLMClient)


def test_complete_mengirim_permintaan_teks_dengan_alamat_dasar_kustom() -> None:
    permintaan: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        permintaan.append(request)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Halo"}}]},
        )

    client = OpenAICompatClient(
        KUNCI,
        "model-uji",
        "https://integrate.api.nvidia.com/v1/",
        transport=httpx.MockTransport(handler),
    )

    assert client.complete("halo") == "Halo"
    assert len(permintaan) == 1
    request = permintaan[0]
    assert request.method == "POST"
    assert str(request.url) == (
        "https://integrate.api.nvidia.com/v1/chat/completions"
    )
    assert request.headers["Authorization"] == f"Bearer {KUNCI}"
    assert request.headers["Content-Type"] == "application/json"
    assert "x-goog-api-key" not in request.headers
    assert KUNCI not in str(request.url)
    assert json.loads(request.content) == {
        "model": "model-uji",
        "messages": [{"role": "user", "content": "halo"}],
    }


def test_complete_menggunakan_alamat_dasar_bawaan() -> None:
    permintaan: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        permintaan.append(request)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Halo"}}]},
        )

    client = OpenAICompatClient(KUNCI, "model-uji", transport=httpx.MockTransport(handler))

    assert client.complete("halo") == "Halo"
    assert str(permintaan[0].url) == "https://api.openai.com/v1/chat/completions"


def test_complete_menggabungkan_bagian_teks_dalam_daftar() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": [
                                {"type": "text", "text": "A"},
                                {"type": "text", "text": "B"},
                            ]
                        }
                    }
                ]
            },
        )

    client = OpenAICompatClient(KUNCI, "model-uji", transport=httpx.MockTransport(handler))

    assert client.complete("halo") == "AB"


@pytest.mark.parametrize(
    "respons",
    [
        httpx.Response(200, json={"choices": []}),
        httpx.Response(200, json={"choices": [{"message": {"content": None}}]}),
        httpx.Response(200, json={"choices": [{"message": {"content": ""}}]}),
        httpx.Response(200, json=[]),
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

    client = OpenAICompatClient(KUNCI, "model-uji", transport=httpx.MockTransport(handler))

    with pytest.raises(LLMError) as galat:
        client.complete("halo")

    assert str(galat.value) == "Balasan AI kosong atau tidak valid"
    assert len(jumlah) == 1
    assert KUNCI not in str(galat.value)


def test_complete_mengulang_503_lalu_berhasil() -> None:
    jumlah: list[int] = []
    tidur: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        jumlah.append(1)
        if len(jumlah) == 1:
            return httpx.Response(503, json={"error": "sibuk"})
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "hasil"}}]},
        )

    client = OpenAICompatClient(
        KUNCI,
        "model-uji",
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

    client = OpenAICompatClient(
        KUNCI,
        "model-uji",
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

    client = OpenAICompatClient(
        KUNCI,
        "model-uji",
        transport=httpx.MockTransport(handler),
        tidur=tidur.append,
    )

    with pytest.raises(LLMError) as galat:
        client.complete("halo")

    assert str(galat.value) == "Layanan AI tidak tersedia (HTTP 500)"
    assert len(jumlah) == 3
    assert tidur == [1, 2]
    assert KUNCI not in str(galat.value)


@pytest.mark.parametrize("kode", [400, 401, 403, 404])
def test_complete_tidak_mengulang_galat_permintaan(kode: int) -> None:
    jumlah: list[int] = []
    tidur: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        jumlah.append(1)
        return httpx.Response(kode, json={"error": "ditolak"})

    client = OpenAICompatClient(
        KUNCI,
        "model-uji",
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

    client = OpenAICompatClient(
        KUNCI,
        "model-uji",
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

    client = OpenAICompatClient(
        KUNCI,
        "model-uji",
        transport=httpx.MockTransport(handler),
        tidur=tidur.append,
    )

    with pytest.raises(LLMError) as galat:
        client.complete("halo")

    assert str(galat.value) == "Koneksi ke AI gagal"
    assert len(jumlah) == 3
    assert tidur == [1, 2]
    assert KUNCI not in str(galat.value)


def test_complete_dengan_gambar_mengirim_gambar_sebagai_data_url(gambar_png: bytes) -> None:
    permintaan: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        permintaan.append(request)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "hasil"}}]},
        )

    client = OpenAICompatClient(
        KUNCI,
        "model-uji",
        "https://contoh.test/v1",
        transport=httpx.MockTransport(handler),
    )

    assert client.complete_dengan_gambar("apa ini", gambar_png, "image/png") == "hasil"
    assert len(permintaan) == 1
    request = permintaan[0]
    assert request.method == "POST"
    assert str(request.url) == "https://contoh.test/v1/chat/completions"
    assert request.headers["Authorization"] == f"Bearer {KUNCI}"
    assert request.headers["Content-Type"] == "application/json"
    assert json.loads(request.content) == {
        "model": "model-uji",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "apa ini"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": (
                                "data:image/png;base64,"
                                + base64.b64encode(gambar_png).decode("ascii")
                            )
                        },
                    },
                ],
            }
        ],
    }


def test_complete_dengan_gambar_mengulang_503_lalu_berhasil(gambar_png: bytes) -> None:
    jumlah: list[int] = []
    tidur: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        jumlah.append(1)
        if len(jumlah) == 1:
            return httpx.Response(503, json={"error": "sibuk"})
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "hasil"}}]},
        )

    client = OpenAICompatClient(
        KUNCI,
        "model-uji",
        transport=httpx.MockTransport(handler),
        tidur=tidur.append,
    )

    assert client.complete_dengan_gambar("apa ini", gambar_png, "image/png") == "hasil"
    assert len(jumlah) == 2
    assert tidur == [1]


def test_complete_dengan_gambar_mengulang_429_sampai_kuota_habis(
    gambar_png: bytes,
) -> None:
    jumlah: list[int] = []
    tidur: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        jumlah.append(1)
        return httpx.Response(429, json={"error": "kuota"})

    client = OpenAICompatClient(
        KUNCI,
        "model-uji",
        transport=httpx.MockTransport(handler),
        tidur=tidur.append,
    )

    with pytest.raises(LLMError) as galat:
        client.complete_dengan_gambar("apa ini", gambar_png, "image/png")

    assert str(galat.value) == "Kuota atau batas laju AI terlampaui (HTTP 429)"
    assert len(jumlah) == 3
    assert tidur == [1, 2]


def test_complete_dengan_gambar_tidak_mengulang_galat_permintaan(
    gambar_png: bytes,
) -> None:
    jumlah: list[int] = []
    tidur: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        jumlah.append(1)
        return httpx.Response(400, json={"error": "ditolak"})

    client = OpenAICompatClient(
        KUNCI,
        "model-uji",
        transport=httpx.MockTransport(handler),
        tidur=tidur.append,
    )

    with pytest.raises(LLMError) as galat:
        client.complete_dengan_gambar("apa ini", gambar_png, "image/png")

    assert str(galat.value) == "Permintaan ke AI ditolak (HTTP 400)"
    assert len(jumlah) == 1
    assert tidur == []


def test_ekstrak_dari_gambar_dengan_openai_compat_sama_dengan_fixture_kaos(
    kaos, gambar_png: bytes, json_kaos: str
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": json_kaos}}]},
        )

    client = OpenAICompatClient(
        KUNCI,
        "model-uji",
        transport=httpx.MockTransport(handler),
    )

    assert ekstrak_dari_gambar(gambar_png, "image/png", client) == kaos
