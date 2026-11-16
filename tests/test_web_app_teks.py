from pathlib import Path

import httpx
from streamlit.testing.v1 import AppTest

from katalogin.llm import FakeLLM
from katalogin.web.tampilan import PLATFORM_OPSI, TONE_OPSI


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

DESKRIPSI = """Halo kak! Kenalin Oneck Kaos Polos Pria.

Spesifikasi:
- Bahan: Katun Combed 30s
- Ukuran: L
- Warna: Hitam
- Fungsi: Harian
- Fitur: Adem, Tidak Mudah Luntur

Yuk, order sekarang, kak!"""

TAGS = (
    "kaos polos pria, oneck kaos polos pria, kaos polos pria hitam, "
    "kaos polos pria katun combed 30s, kaos polos pria harian, adem, "
    "tidak mudah luntur"
)

APP_WEB = Path(__file__).resolve().parents[1] / "katalogin" / "web" / "app.py"


def test_tanpa_id_pengguna_menampilkan_petunjuk_dan_tidak_membuat_tab(
    buat_app_web,
) -> None:
    at = buat_app_web(user_id="")

    assert len(at.exception) == 0
    assert at.info[0].value == "Isi ID pengguna di sidebar untuk mulai."
    assert len(at.tabs) == 0


def test_sidebar_menampilkan_kredit_dan_opsi_platform_tone(buat_app_web) -> None:
    at = buat_app_web()

    assert len(at.exception) == 0
    assert [tab.label for tab in at.tabs] == [
        "Dari teks",
        "Dari foto",
        "Dari CSV",
        "Riwayat",
    ]
    assert at.sidebar.metric[0].label == "Kredit"
    assert at.sidebar.metric[0].value == "5"
    assert at.sidebar.selectbox(key="platform").options == PLATFORM_OPSI
    assert at.sidebar.selectbox(key="tone").options == TONE_OPSI


def test_membuat_listing_dari_teks_menampilkan_hasil_dan_mengurangi_kredit(
    buat_app_web,
) -> None:
    at = buat_app_web()

    at.text_area(key="teks_mentah").set_value(TEKS_ONECK)
    at.button(key="btn_teks").click()
    at.run()

    assert [code.value for code in at.tabs[0].code] == JUDUL + [DESKRIPSI, TAGS]
    assert [caption.value for caption in at.tabs[0].caption] == [
        "Teks asli",
        "Judul 1 (40/255 karakter)",
        "Judul 2 (44/255 karakter)",
        "Judul 3 (34/255 karakter)",
        "Deskripsi",
        "Tag",
    ]
    assert at.sidebar.metric[0].value == "4"
    assert len(at.error) == 0
    assert at.session_state["hasil_teks"]["teks"] == TEKS_ONECK
    assert at.session_state["hasil_teks"]["respons"]["sisa_kredit"] == 4


def test_teks_kosong_menampilkan_galat_dan_tidak_membuat_blok_kode(
    buat_app_web,
) -> None:
    at = buat_app_web()

    at.text_area(key="teks_mentah").set_value("   ")
    at.button(key="btn_teks").click()
    at.run()

    assert at.error[0].value == "Isi teks produk terlebih dahulu."
    assert len(at.tabs[0].code) == 0
    assert "hasil_teks" not in at.session_state


def test_batas_karakter_judul_mengikuti_platform(buat_app_web) -> None:
    at = buat_app_web()

    at.sidebar.selectbox(key="platform").set_value("tokopedia")
    at.run()
    at.text_area(key="teks_mentah").set_value(TEKS_ONECK)
    at.button(key="btn_teks").click()
    at.run()

    assert [caption.value for caption in at.tabs[0].caption] == [
        "Teks asli",
        "Judul 1 (40/70 karakter)",
        "Judul 2 (44/70 karakter)",
        "Judul 3 (34/70 karakter)",
        "Deskripsi",
        "Tag",
    ]


def test_ekstraksi_ai_menampilkan_jenis_ekstraksi(buat_app_web, json_kaos) -> None:
    at = buat_app_web(llm=FakeLLM(json_kaos))

    at.checkbox(key="gunakan_ai").set_value(True)
    at.text_area(key="teks_mentah").set_value("kaos oneck hitam")
    at.button(key="btn_teks").click()
    at.run()

    assert "Ekstraksi: ai" in [
        caption.value for caption in at.tabs[0].caption
    ]
    assert at.sidebar.metric[0].value == "4"


def test_ekstraksi_ai_gagal_jatuh_ke_aturan(buat_app_web) -> None:
    at = buat_app_web(llm=FakeLLM("bukan json"))

    at.checkbox(key="gunakan_ai").set_value(True)
    at.text_area(key="teks_mentah").set_value("KAOS POLOS PRIA\nwrn: htm")
    at.button(key="btn_teks").click()
    at.run()

    assert "Ekstraksi: aturan" in [
        caption.value for caption in at.tabs[0].caption
    ]


def test_nama_produk_tidak_ditemukan_menampilkan_galat_dan_tidak_mengubah_kredit(
    buat_app_web,
) -> None:
    at = buat_app_web()

    at.text_area(key="teks_mentah").set_value("merek: Oneck")
    at.button(key="btn_teks").click()
    at.run()

    assert at.error[0].value == "Nama produk tidak ditemukan"
    assert at.sidebar.metric[0].value == "5"
    assert "hasil_teks" not in at.session_state


def test_ai_tanpa_konfigurasi_menampilkan_galat(buat_app_web) -> None:
    at = buat_app_web()

    at.checkbox(key="gunakan_ai").set_value(True)
    at.text_area(key="teks_mentah").set_value("kaos oneck hitam")
    at.button(key="btn_teks").click()
    at.run()

    assert at.error[0].value == "Layanan AI belum dikonfigurasi"
    assert at.sidebar.metric[0].value == "5"


def test_kredit_habis_ditampilkan_saat_generate_ke_enam(buat_app_web) -> None:
    at = buat_app_web()

    for _ in range(5):
        at.text_area(key="teks_mentah").set_value(TEKS_ONECK)
        at.button(key="btn_teks").click()
        at.run()

    at.text_area(key="teks_mentah").set_value(TEKS_ONECK)
    at.button(key="btn_teks").click()
    at.run()

    assert at.error[0].value == (
        "Kredit tidak cukup: butuh 1, tersisa 0. "
        "Kredit habis; hubungi admin untuk menambah kredit."
    )
    assert at.sidebar.metric[0].value == "0"
    assert "hasil_teks" not in at.session_state


def test_gagal_koneksi_api_ditampilkan_di_sidebar(buat_app_web) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("koneksi gagal")

    http = httpx.Client(
        base_url="http://api.test",
        transport=httpx.MockTransport(handler),
    )
    at = buat_app_web(http=http)

    assert len(at.exception) == 0
    assert at.sidebar.error[0].value == "Tidak bisa terhubung ke server API"


def test_alamat_api_tidak_valid_ditampilkan_di_halaman(
    monkeypatch,
) -> None:
    monkeypatch.setenv("KATALOGIN_API_URL", "ftp://x")

    at = AppTest.from_file(str(APP_WEB), default_timeout=30)
    at.run()

    assert len(at.exception) == 0
    assert at.error[0].value == (
        "KATALOGIN_API_URL harus diawali http:// atau https://"
    )
