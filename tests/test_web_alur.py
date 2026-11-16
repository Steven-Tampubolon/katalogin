from katalogin.llm import FakeLLM


TEKS_ONECK = """KAOS POLOS PRIA
Brand: Oneck
bhn: ktn combed 30s
uk: L
wrn: htm
kegunaan: harian
keunggulan: adem, tidak mudah luntur"""

CSV_DUA_PRODUK = b"nama,merek\nKaos Polos Pria,Oneck\nTas Ransel,Bagus\n"


def test_alur_lengkap_teks_foto_csv_riwayat_dan_hashtag(
    buat_app_web, json_kaos, gambar_png
) -> None:
    at = buat_app_web(llm=FakeLLM(json_kaos))

    at.text_area(key="teks_mentah").set_value(TEKS_ONECK)
    at.button(key="btn_teks").click()
    at.run()

    at.file_uploader(key="unggah_foto").upload("kaos.png", gambar_png, "image/png")
    at.run()
    at.button(key="btn_foto").click()
    at.run()

    at.file_uploader(key="unggah_csv").upload(
        "produk.csv", CSV_DUA_PRODUK, "text/csv"
    )
    at.run()
    at.button(key="btn_csv").click()
    at.run()

    assert len(at.exception) == 0
    assert at.sidebar.metric[0].value == "1"
    assert [
        baris["ID"]
        for baris in at.tabs[3].dataframe[0].value.to_dict("records")
    ] == [4, 3, 2, 1]

    at.sidebar.selectbox(key="platform").set_value("tiktok")
    at.run()
    at.text_area(key="teks_mentah").set_value(TEKS_ONECK)
    at.button(key="btn_teks").click()
    at.run()

    assert len(at.exception) == 0
    assert at.tabs[0].code[4].value.startswith("#")
    assert at.sidebar.metric[0].value == "0"
