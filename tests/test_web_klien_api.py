import base64
import json

import httpx
import pytest

from katalogin.llm import FakeLLM
from katalogin.web.klien_api import ApiError, KlienApi, buat_http_dari_env


TEKS_ONECK = """KAOS POLOS PRIA
Brand: Oneck
bhn: ktn combed 30s
uk: L
wrn: htm
kegunaan: harian
keunggulan: adem, tidak mudah luntur"""

JUDUL = [
    "Oneck Kaos Polos Pria Katun Combed 30s L",
    "Kaos Polos Pria Oneck Hitam Katun Combed 30s",
    "Oneck Kaos Polos Pria Hitam L Adem",
]


def test_buat_http_dari_env_memakai_alamat_bawaan_dan_timeout() -> None:
    http = buat_http_dari_env({})

    assert str(http.base_url) == "http://127.0.0.1:8000"
    assert http.timeout.read == 120.0

    http.close()


def test_buat_http_dari_env_membersihkan_alamat() -> None:
    http = buat_http_dari_env({"KATALOGIN_API_URL": " https://api.contoh.id/ "})

    assert str(http.base_url) == "https://api.contoh.id"

    http.close()


def test_buat_http_dari_env_menolak_alamat_tanpa_http() -> None:
    with pytest.raises(
        ValueError,
        match="^KATALOGIN_API_URL harus diawali http:// atau https://$",
    ):
        buat_http_dari_env({"KATALOGIN_API_URL": "ftp://x"})


def test_api_error_menyimpan_status_detail_dan_pesan() -> None:
    galat = ApiError(422, "Masukan tidak valid")

    assert galat.status == 422
    assert galat.detail == "Masukan tidak valid"
    assert str(galat) == "Masukan tidak valid"


def test_kredit_mengembalikan_saldo(klien) -> None:
    api = KlienApi(klien, "andi")

    assert api.kredit() == 5


def test_generate_teks_dan_riwayat_menggunakan_api(klien) -> None:
    api = KlienApi(klien, "andi")

    respons = api.generate_teks(TEKS_ONECK, "shopee", "kasual")

    assert respons["hasil"]["judul"] == JUDUL
    assert respons["sisa_kredit"] == 4
    assert respons["id"] == 1

    daftar = api.riwayat()

    assert daftar["total"] == 1

    detail = api.riwayat_item(1)

    assert detail["hasil"]["nama_produk"] == "Kaos Polos Pria"


def test_generate_teks_foto_dan_csv_dengan_ai(klien, buat_klien_ai, json_kaos, gambar_png) -> None:
    llm = FakeLLM(json_kaos)
    api = KlienApi(buat_klien_ai(llm), "andi")

    teks = api.generate_teks("kaos oneck", "shopee", "kasual", gunakan_ai=True)
    foto = api.generate_foto(gambar_png, "shopee", "kasual")
    csv = api.generate_csv(
        "nama,merek\nKaos,Oneck\nTas,Bagus",
        "shopee",
        "kasual",
    )

    assert teks["ekstraksi"] == "ai"
    assert foto["ekstraksi"] == "foto"
    assert llm.gambar[0][1] == gambar_png
    assert len(csv["hasil"]) == 2
    assert csv["csv"].splitlines()[0] == (
        "nama_produk,platform,tone,judul_1,judul_2,judul_3,deskripsi,tags,"
        "peringatan"
    )


def test_generate_teks_melempar_api_error_untuk_nama_yang_tidak_ditemukan(klien) -> None:
    api = KlienApi(klien, "andi")

    with pytest.raises(ApiError) as konteks:
        api.generate_teks("merek: Oneck", "shopee", "kasual")

    assert konteks.value.status == 400
    assert konteks.value.detail == "Nama produk tidak ditemukan"


def test_generate_teks_melempar_api_error_untuk_kredit_tidak_cukup(klien) -> None:
    api = KlienApi(klien, "andi")

    for _ in range(5):
        api.generate_teks(TEKS_ONECK, "shopee", "kasual")

    with pytest.raises(ApiError) as konteks:
        api.generate_teks(TEKS_ONECK, "shopee", "kasual")

    assert konteks.value.status == 402
    assert konteks.value.detail == "Kredit tidak cukup: butuh 1, tersisa 0"


def test_riwayat_item_tidak_ditemukan_melempar_api_error(klien) -> None:
    api = KlienApi(klien, "andi")

    with pytest.raises(ApiError) as konteks:
        api.riwayat_item(999)

    assert konteks.value.status == 404
    assert konteks.value.detail == "Riwayat tidak ditemukan"


def test_masukan_terlalu_panjang_melempar_api_error_validasi(klien) -> None:
    api = KlienApi(klien, "andi")

    with pytest.raises(ApiError) as konteks:
        api.generate_teks("a" * 20001, "shopee", "kasual")

    assert konteks.value.status == 422
    assert konteks.value.detail == "Masukan tidak valid"


def test_user_id_tidak_valid_melempar_api_error(klien) -> None:
    api = KlienApi(klien, "a b")

    with pytest.raises(ApiError) as konteks:
        api.kredit()

    assert konteks.value.status == 400
    assert konteks.value.detail == "X-User-Id tidak valid"


def test_semua_permintaan_mengirim_header_dan_body_yang_benar() -> None:
    permintaan: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        permintaan.append(request)
        return httpx.Response(200, json={"kredit": 5, "hasil": [], "total": 0})

    with httpx.Client(
        base_url="http://api.test",
        transport=httpx.MockTransport(handler),
    ) as http:
        api = KlienApi(http, "andi")
        api.kredit()
        api.generate_teks("teks", "shopee", "kasual")
        api.generate_foto(b"data gambar", "shopee", "kasual")
        api.generate_csv("nama\nKaos", "shopee", "kasual")
        api.riwayat(limit=10, offset=2)
        api.riwayat_item(7)

    assert len(permintaan) == 6
    assert all(request.headers["X-User-Id"] == "andi" for request in permintaan)
    assert json.loads(permintaan[1].content) == {
        "platform": "shopee",
        "tone": "kasual",
        "teks": "teks",
        "gunakan_ai": False,
    }
    assert json.loads(permintaan[2].content)["gambar_base64"] == (
        base64.b64encode(b"data gambar").decode("ascii")
    )
    assert json.loads(permintaan[3].content) == {
        "platform": "shopee",
        "tone": "kasual",
        "csv": "nama\nKaos",
    }
    assert dict(permintaan[4].url.params) == {"limit": "10", "offset": "2"}
    assert permintaan[5].url.path == "/riwayat/7"


@pytest.mark.parametrize(
    ("galat", "detail"),
    [
        (httpx.ConnectError("koneksi gagal"), "Tidak bisa terhubung ke server API"),
        (httpx.ReadTimeout("waktu habis"), "Server API tidak menjawab (waktu habis)"),
    ],
)
def test_galat_transport_menjadi_api_error(
    galat: httpx.TransportError,
    detail: str,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise galat

    with httpx.Client(
        base_url="http://api.test",
        transport=httpx.MockTransport(handler),
    ) as http:
        api = KlienApi(http, "andi")

        with pytest.raises(ApiError) as konteks:
            api.kredit()

    assert konteks.value.status == 0
    assert konteks.value.detail == detail


@pytest.mark.parametrize(
    ("status", "isi", "detail"),
    [
        (500, "galat server", "Galat server (HTTP 500)"),
        (422, '{"detail": [{"msg": "x"}]}', "Masukan tidak valid"),
    ],
)
def test_respons_galat_menjadi_api_error(status: int, isi: str, detail: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, text=isi)

    with httpx.Client(
        base_url="http://api.test",
        transport=httpx.MockTransport(handler),
    ) as http:
        api = KlienApi(http, "andi")

        with pytest.raises(ApiError) as konteks:
            api.kredit()

    assert konteks.value.status == status
    assert konteks.value.detail == detail
