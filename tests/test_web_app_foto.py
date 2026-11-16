import dataclasses
import json

from katalogin.llm import FakeLLM, LLMError
from katalogin.web.klien_api import KlienApi


JUDUL_PERTAMA = "Oneck Kaos Polos Pria Katun Combed 30s L"


def test_tanpa_foto_menampilkan_galat_dan_tidak_memanggil_api(buat_app_web) -> None:
    at = buat_app_web()

    at.button(key="btn_foto").click()
    at.run()

    assert at.error[0].value == "Pilih foto produk terlebih dahulu."
    assert len(at.exception) == 0
    assert "hasil_foto" not in at.session_state


def test_foto_berhasil_menampilkan_produk_dan_hasil(
    buat_app_web, json_kaos, kaos, gambar_png
) -> None:
    llm = FakeLLM(json_kaos)
    at = buat_app_web(llm=llm)

    at.file_uploader(key="unggah_foto").upload("kaos.png", gambar_png, "image/png")
    at.run()

    assert "kaos.png (40 byte)" in [
        caption.value for caption in at.tabs[1].caption
    ]

    at.button(key="btn_foto").click()
    at.run()

    assert len(at.exception) == 0
    assert at.tabs[1].code[0].value == JUDUL_PERTAMA
    assert json.loads(at.tabs[1].json[0].value) == dataclasses.asdict(kaos)
    assert "Produk terbaca dari foto (periksa sebelum dipakai)" in [
        caption.value for caption in at.tabs[1].caption
    ]
    assert at.sidebar.metric[0].value == "4"
    assert llm.gambar[0][1] == gambar_png
    assert at.session_state["hasil_foto"]["sisa_kredit"] == 4


def test_foto_terlalu_besar_menampilkan_galat_tanpa_memanggil_api(
    buat_app_web, monkeypatch, gambar_png
) -> None:
    llm = FakeLLM("{}")

    def gagal_jika_dipanggil(*args, **kwargs):
        raise AssertionError("generate_foto tidak boleh dipanggil")

    monkeypatch.setattr(KlienApi, "generate_foto", gagal_jika_dipanggil)
    at = buat_app_web(llm=llm)

    at.file_uploader(key="unggah_foto").upload(
        "kaos.png", gambar_png + b"\x00" * 5_000_000, "image/png"
    )
    at.run()
    at.button(key="btn_foto").click()
    at.run()

    assert len(at.exception) == 0
    assert at.error[0].value == "Gambar terlalu besar (maksimum 5 MB)"
    assert llm.gambar == []
    assert at.sidebar.metric[0].value == "5"
    assert "hasil_foto" not in at.session_state


def test_llm_gagal_menampilkan_galat_dan_kredit_tetap(
    buat_app_web, gambar_png
) -> None:
    llm = FakeLLM(LLMError("kuota habis"))
    at = buat_app_web(llm=llm)

    at.file_uploader(key="unggah_foto").upload("kaos.png", gambar_png, "image/png")
    at.run()
    at.button(key="btn_foto").click()
    at.run()

    assert at.error[0].value == "Layanan AI gagal: kuota habis"
    assert at.sidebar.metric[0].value == "5"
    assert "hasil_foto" not in at.session_state


def test_tanpa_ai_menampilkan_galat(buat_app_web, gambar_png) -> None:
    at = buat_app_web()

    at.file_uploader(key="unggah_foto").upload("kaos.png", gambar_png, "image/png")
    at.run()
    at.button(key="btn_foto").click()
    at.run()

    assert at.error[0].value == "Layanan AI belum dikonfigurasi"
    assert at.sidebar.metric[0].value == "5"
    assert "hasil_foto" not in at.session_state


def test_json_foto_tidak_valid_menampilkan_galat(buat_app_web, gambar_png) -> None:
    at = buat_app_web(llm=FakeLLM("bukan json"))

    at.file_uploader(key="unggah_foto").upload("kaos.png", gambar_png, "image/png")
    at.run()
    at.button(key="btn_foto").click()
    at.run()

    assert at.error[0].value == "Gagal membaca produk dari gambar"
    assert at.sidebar.metric[0].value == "5"
    assert "hasil_foto" not in at.session_state


def test_foto_gagal_menghapus_hasil_foto_sebelumnya(
    buat_app_web, json_kaos, gambar_png
) -> None:
    llm = FakeLLM(json_kaos)
    at = buat_app_web(llm=llm)

    at.file_uploader(key="unggah_foto").upload("kaos.png", gambar_png, "image/png")
    at.run()
    at.button(key="btn_foto").click()
    at.run()

    assert "hasil_foto" in at.session_state

    llm.respons = LLMError("kuota habis")
    at.button(key="btn_foto").click()
    at.run()

    assert at.error[0].value == "Layanan AI gagal: kuota habis"
    assert "hasil_foto" not in at.session_state
