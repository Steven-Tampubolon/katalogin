from katalogin.web.klien_api import ApiError, KlienApi


def buat_listing_dari_teks(at, teks: str) -> None:
    at.text_area(key="teks_mentah").set_value(teks)
    at.button(key="btn_teks").click()
    at.run()


def buat_riwayat_langsung(http, user_id: str, nama: str) -> None:
    respons = http.post(
        "/generate",
        headers={"X-User-Id": user_id},
        json={"platform": "shopee", "produk": {"nama": nama}},
    )

    assert respons.status_code == 200


def test_pengguna_baru_menampilkan_tidak_ada_riwayat(buat_app_web) -> None:
    at = buat_app_web()

    assert len(at.exception) == 0
    assert at.tabs[3].info[0].value == "Belum ada riwayat."


def test_riwayat_menampilkan_item_terbaru_dan_memilih_detail(
    buat_app_web,
) -> None:
    at = buat_app_web()

    for teks in ("KAOS A", "TAS B", "SEPATU C"):
        buat_listing_dari_teks(at, teks)

    tab_riwayat = at.tabs[3]
    assert len(at.exception) == 0
    assert [
        baris["ID"]
        for baris in tab_riwayat.dataframe[0].value.to_dict("records")
    ] == [3, 2, 1]
    assert tab_riwayat.caption[0].value == "3 terbaru dari 3 riwayat"
    assert at.selectbox(key="pilih_riwayat").value == 3
    assert "**Sepatu C**" in [markdown.value for markdown in tab_riwayat.markdown]

    at.selectbox(key="pilih_riwayat").select(1)
    at.run()

    assert at.selectbox(key="pilih_riwayat").value == 1
    assert "**Kaos A**" in [markdown.value for markdown in at.tabs[3].markdown]

    buat_listing_dari_teks(at, "KAOS D")

    assert at.tabs[3].selectbox(key="pilih_riwayat").value == 4


def test_ganti_pengguna_menghapus_hasil_lama_dan_memilih_riwayat_terbaru(
    buat_app_web,
) -> None:
    at = buat_app_web()
    for teks in ("KAOS A", "TAS B", "SEPATU C", "KAOS D"):
        buat_listing_dari_teks(at, teks)

    http = at.session_state["http_klien"]
    for nomor in range(1, 5):
        buat_riwayat_langsung(http, "siti", f"SITI {nomor}")

    at.sidebar.text_input(key="user_id").set_value("siti")
    at.run()

    assert len(at.exception) == 0
    assert at.tabs[3].selectbox(key="pilih_riwayat").value == 8
    assert "**SITI 4**" in [markdown.value for markdown in at.tabs[3].markdown]

    at.sidebar.text_input(key="user_id").set_value("andi")
    at.run()

    assert len(at.exception) == 0
    assert at.tabs[3].selectbox(key="pilih_riwayat").value == 4
    assert "**Kaos D**" in [markdown.value for markdown in at.tabs[3].markdown]


def test_pengguna_baru_menghapus_hasil_lama_dan_menampilkan_kredit_bawaan(
    buat_app_web,
) -> None:
    at = buat_app_web()
    buat_listing_dari_teks(at, "KAOS A")

    at.sidebar.text_input(key="user_id").set_value("siti")
    at.run()

    assert len(at.exception) == 0
    assert len(at.tabs[0].code) == 0
    assert at.sidebar.metric[0].value == "5"
    assert at.tabs[3].info[0].value == "Belum ada riwayat."


def test_riwayat_membatasi_tampilan_pada_20_item_terbaru(buat_app_web) -> None:
    at = buat_app_web()
    http = at.session_state["http_klien"]
    respons = http.post(
        "/admin/kredit",
        headers={"X-Admin-Token": "token-uji"},
        json={"user_id": "andi", "jumlah": 30},
    )
    assert respons.status_code == 200

    for nomor in range(1, 26):
        buat_riwayat_langsung(http, "andi", f"Kaos {nomor}")

    at.run()

    tab_riwayat = at.tabs[3]
    assert len(at.exception) == 0
    assert tab_riwayat.caption[0].value == "20 terbaru dari 25 riwayat"
    assert len(tab_riwayat.dataframe[0].value) == 20
    assert at.sidebar.metric[0].value == "10"


def test_galat_mengambil_riwayat_ditampilkan_di_tab_riwayat(
    buat_app_web, monkeypatch
) -> None:
    def gagal(self, limit: int = 20, offset: int = 0) -> dict:
        raise ApiError(500, "Galat riwayat")

    monkeypatch.setattr(KlienApi, "riwayat", gagal)
    at = buat_app_web()

    assert len(at.exception) == 0
    assert at.tabs[3].error[0].value == "Galat riwayat"
