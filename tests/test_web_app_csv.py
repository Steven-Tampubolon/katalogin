from katalogin.llm import FakeLLM
from katalogin.web.klien_api import KlienApi


CSV_DUA_PRODUK = b"nama,merek\nKaos Polos Pria,Oneck\nTas Ransel,Bagus\n"


def test_tanpa_csv_menampilkan_galat_dan_tidak_memanggil_api(
    buat_app_web, monkeypatch
) -> None:
    def gagal_jika_dipanggil(*args, **kwargs):
        raise AssertionError("generate_csv tidak boleh dipanggil")

    monkeypatch.setattr(KlienApi, "generate_csv", gagal_jika_dipanggil)
    at = buat_app_web()

    at.button(key="btn_csv").click()
    at.run()

    assert at.error[0].value == "Pilih berkas CSV terlebih dahulu."
    assert len(at.exception) == 0
    assert "hasil_csv" not in at.session_state


def test_csv_berhasil_menampilkan_tabel_expander_dan_tombol_unduh(
    buat_app_web, json_kaos
) -> None:
    at = buat_app_web(llm=FakeLLM(json_kaos))

    at.file_uploader(key="unggah_csv").upload("p.csv", CSV_DUA_PRODUK, "text/csv")
    at.run()
    at.button(key="btn_csv").click()
    at.run()

    assert len(at.exception) == 0
    assert at.tabs[2].dataframe[0].value.to_dict("records") == [
        {
            "Produk": "Kaos Polos Pria",
            "Judul 1": "Oneck Kaos Polos Pria",
            "Judul 2": "Kaos Polos Pria Oneck",
            "Judul 3": "",
            "Tag": "kaos polos pria, oneck kaos polos pria",
            "Peringatan": "",
        },
        {
            "Produk": "Tas Ransel",
            "Judul 1": "Bagus Tas Ransel",
            "Judul 2": "Tas Ransel Bagus",
            "Judul 3": "",
            "Tag": "tas ransel, bagus tas ransel",
            "Peringatan": "",
        },
    ]
    assert [expander.label for expander in at.tabs[2].expander] == [
        "Kaos Polos Pria",
        "Tas Ransel",
    ]
    assert len(at.tabs[2].download_button) == 1
    assert at.tabs[2].download_button[0].label == "Unduh CSV hasil"
    assert at.session_state["hasil_csv"]["csv"].splitlines()[0] == (
        "nama_produk,platform,tone,judul_1,judul_2,judul_3,deskripsi,tags,peringatan"
    )
    assert at.sidebar.metric[0].value == "3"


def test_hasil_csv_tetap_tampil_saat_tone_berubah_tanpa_panggilan_api(
    buat_app_web, json_kaos, monkeypatch
) -> None:
    at = buat_app_web(llm=FakeLLM(json_kaos))
    at.file_uploader(key="unggah_csv").upload("p.csv", CSV_DUA_PRODUK, "text/csv")
    at.run()
    at.button(key="btn_csv").click()
    at.run()

    def gagal_jika_dipanggil(*args, **kwargs):
        raise AssertionError("generate_csv tidak boleh dipanggil")

    monkeypatch.setattr(KlienApi, "generate_csv", gagal_jika_dipanggil)
    at.sidebar.selectbox(key="tone").set_value("singkat")
    at.run()

    assert len(at.tabs[2].dataframe) == 1
    assert at.sidebar.metric[0].value == "3"


def test_csv_bukan_utf8_menampilkan_galat_tanpa_memanggil_api(
    buat_app_web, monkeypatch
) -> None:
    def gagal_jika_dipanggil(*args, **kwargs):
        raise AssertionError("generate_csv tidak boleh dipanggil")

    monkeypatch.setattr(KlienApi, "generate_csv", gagal_jika_dipanggil)
    at = buat_app_web()
    at.file_uploader(key="unggah_csv").upload(
        "p.csv", b"\xff\xfe\x00bad", "text/csv"
    )
    at.run()
    at.button(key="btn_csv").click()
    at.run()

    assert at.error[0].value == "Berkas CSV harus berkode UTF-8."
    assert at.sidebar.metric[0].value == "5"
    assert "hasil_csv" not in at.session_state


def test_csv_tanpa_kolom_nama_menampilkan_galat_dan_kredit_tetap(
    buat_app_web,
) -> None:
    at = buat_app_web()
    at.file_uploader(key="unggah_csv").upload(
        "p.csv", b"merek\nOneck\n", "text/csv"
    )
    at.run()
    at.button(key="btn_csv").click()
    at.run()

    assert at.error[0].value == "Kolom 'nama' wajib ada"
    assert at.sidebar.metric[0].value == "5"
    assert "hasil_csv" not in at.session_state


def test_csv_lebih_dari_20_baris_menampilkan_galat_dan_kredit_tetap(
    buat_app_web,
) -> None:
    csv_terlalu_banyak = (
        "nama\n" + "".join(f"Produk {nomor}\n" for nomor in range(1, 22))
    ).encode()
    at = buat_app_web()
    at.file_uploader(key="unggah_csv").upload(
        "p.csv", csv_terlalu_banyak, "text/csv"
    )
    at.run()
    at.button(key="btn_csv").click()
    at.run()

    assert at.error[0].value == "Maksimum 20 baris, ditemukan 21"
    assert at.sidebar.metric[0].value == "5"
    assert "hasil_csv" not in at.session_state


def test_csv_enam_baris_menampilkan_galat_kredit_tidak_cukup(
    buat_app_web,
) -> None:
    csv_enam_produk = (
        "nama\n" + "".join(f"Produk {nomor}\n" for nomor in range(1, 7))
    ).encode()
    at = buat_app_web()
    at.file_uploader(key="unggah_csv").upload(
        "p.csv", csv_enam_produk, "text/csv"
    )
    at.run()
    at.button(key="btn_csv").click()
    at.run()

    assert at.error[0].value == (
        "Kredit tidak cukup: butuh 6, tersisa 5. "
        "Kredit habis; hubungi admin untuk menambah kredit."
    )
    assert at.sidebar.metric[0].value == "5"
    assert "hasil_csv" not in at.session_state


def test_csv_gagal_menghapus_hasil_csv_sebelumnya(
    buat_app_web, json_kaos
) -> None:
    at = buat_app_web(llm=FakeLLM(json_kaos))
    at.file_uploader(key="unggah_csv").upload("p.csv", CSV_DUA_PRODUK, "text/csv")
    at.run()
    at.button(key="btn_csv").click()
    at.run()

    assert "hasil_csv" in at.session_state

    at.file_uploader(key="unggah_csv").upload(
        "p.csv", b"merek\nOneck\n", "text/csv"
    )
    at.run()
    at.button(key="btn_csv").click()
    at.run()

    assert at.error[0].value == "Kolom 'nama' wajib ada"
    assert "hasil_csv" not in at.session_state
