import sys
from pathlib import Path


AKAR_REPO = Path(__file__).resolve().parents[2]
if str(AKAR_REPO) not in sys.path:
    sys.path.insert(0, str(AKAR_REPO))

import streamlit as st

from katalogin.web.komponen import tampilkan_hasil
from katalogin.web.klien_api import ApiError, KlienApi, buat_http_dari_env
from katalogin.web.tampilan import (
    PLATFORM_OPSI,
    TONE_OPSI,
    baris_hasil_csv,
    baris_riwayat,
    pesan_galat,
)


st.set_page_config(page_title="Katalogin", layout="wide")
st.title("Katalogin")


@st.cache_resource
def http_bersama():
    return buat_http_dari_env()


try:
    http = st.session_state.get("http_klien")
    if http is None:
        http = http_bersama()
except ValueError as galat:
    st.error(str(galat))
    st.stop()

user_id = st.sidebar.text_input("ID pengguna", key="user_id").strip()
kredit_slot = st.sidebar.empty()
platform = st.sidebar.selectbox("Marketplace", PLATFORM_OPSI, key="platform")
tone = st.sidebar.selectbox("Gaya bahasa", TONE_OPSI, key="tone")

if not user_id:
    st.info("Isi ID pengguna di sidebar untuk mulai.")
    st.stop()

if st.session_state.get("_uid_aktif") != user_id:
    for kunci in (
        "hasil_teks",
        "hasil_foto",
        "hasil_csv",
        "_riwayat_total",
        "pilih_riwayat",
    ):
        st.session_state.pop(kunci, None)
    st.session_state["_uid_aktif"] = user_id

api = KlienApi(http, user_id)
tab_teks, tab_foto, tab_csv, tab_riwayat = st.tabs(
    ["Dari teks", "Dari foto", "Dari CSV", "Riwayat"]
)

with tab_teks:
    teks = st.text_area("Teks mentah dari supplier", key="teks_mentah")
    gunakan_ai = st.checkbox("Pakai AI untuk membaca teks", key="gunakan_ai")

    if st.button("Buat listing", key="btn_teks"):
        if not teks.strip():
            st.error("Isi teks produk terlebih dahulu.")
        else:
            try:
                respons = api.generate_teks(teks, platform, tone, gunakan_ai)
            except ApiError as galat:
                st.session_state.pop("hasil_teks", None)
                st.error(pesan_galat(galat))
            else:
                st.session_state["hasil_teks"] = {"teks": teks, "respons": respons}

    if "hasil_teks" in st.session_state:
        hasil_teks = st.session_state["hasil_teks"]
        respons = hasil_teks["respons"]
        kolom_kiri, kolom_kanan = st.columns(2)
        with kolom_kiri:
            st.caption("Teks asli")
            st.text(hasil_teks["teks"])
        with kolom_kanan:
            tampilkan_hasil(respons["hasil"])
            if "ekstraksi" in respons:
                st.caption(f"Ekstraksi: {respons['ekstraksi']}")

with tab_foto:
    foto = st.file_uploader(
        "Foto produk (JPEG, PNG, atau WebP, maksimum 5 MB)",
        type=["jpg", "jpeg", "png", "webp"],
        key="unggah_foto",
    )
    data_foto = foto.getvalue() if foto is not None else None
    if foto is not None:
        st.caption(f"{foto.name} ({len(data_foto)} byte)")

    if st.button("Baca foto dan buat listing", key="btn_foto"):
        st.session_state.pop("hasil_foto", None)
        if foto is None:
            st.error("Pilih foto produk terlebih dahulu.")
        elif len(data_foto) > 5_000_000:
            st.error("Gambar terlalu besar (maksimum 5 MB)")
        else:
            try:
                respons = api.generate_foto(data_foto, platform, tone)
            except ApiError as galat:
                st.error(pesan_galat(galat))
            else:
                st.session_state["hasil_foto"] = respons

    if "hasil_foto" in st.session_state:
        respons = st.session_state["hasil_foto"]
        st.caption("Produk terbaca dari foto (periksa sebelum dipakai)")
        st.json(respons["produk_terbaca"])
        tampilkan_hasil(respons["hasil"])

with tab_csv:
    berkas_csv = st.file_uploader(
        "Berkas CSV (maksimum 20 baris)",
        type=["csv"],
        key="unggah_csv",
    )

    if st.button("Buat listing dari CSV", key="btn_csv"):
        st.session_state.pop("hasil_csv", None)
        if berkas_csv is None:
            st.error("Pilih berkas CSV terlebih dahulu.")
        else:
            try:
                isi_csv = berkas_csv.getvalue().decode("utf-8-sig")
            except UnicodeDecodeError:
                st.error("Berkas CSV harus berkode UTF-8.")
            else:
                try:
                    respons = api.generate_csv(isi_csv, platform, tone)
                except ApiError as galat:
                    st.error(pesan_galat(galat))
                else:
                    st.session_state["hasil_csv"] = respons

    if "hasil_csv" in st.session_state:
        respons = st.session_state["hasil_csv"]
        st.dataframe(baris_hasil_csv(respons["hasil"]))
        st.download_button(
            "Unduh CSV hasil",
            data=respons["csv"],
            file_name="katalogin-hasil.csv",
            mime="text/csv",
            key="unduh_csv",
        )
        for hasil in respons["hasil"]:
            with st.expander(hasil["nama_produk"]):
                tampilkan_hasil(hasil)

with tab_riwayat:
    try:
        respons_riwayat = api.riwayat(limit=20, offset=0)
    except ApiError as galat:
        st.error(pesan_galat(galat))
    else:
        total = respons_riwayat["total"]
        item = respons_riwayat["item"]
        if total == 0:
            st.session_state["_riwayat_total"] = 0
            st.session_state.pop("pilih_riwayat", None)
            st.info("Belum ada riwayat.")
        else:
            daftar_id = [entri["id"] for entri in item]
            total_sebelumnya = st.session_state.get("_riwayat_total")
            pilihan_sebelumnya = st.session_state.get("pilih_riwayat")
            if (
                total_sebelumnya != total
                or pilihan_sebelumnya not in daftar_id
            ):
                st.session_state["pilih_riwayat"] = daftar_id[0]
            st.session_state["_riwayat_total"] = total

            st.caption(f"{len(item)} terbaru dari {total} riwayat")
            st.dataframe(baris_riwayat(item))
            riwayat_id = st.selectbox(
                "Lihat detail",
                daftar_id,
                key="pilih_riwayat",
            )

            try:
                detail = api.riwayat_item(riwayat_id)
            except ApiError as galat:
                st.error(pesan_galat(galat))
            else:
                tampilkan_hasil(detail["hasil"])

try:
    kredit = api.kredit()
except ApiError as galat:
    kredit_slot.error(pesan_galat(galat))
else:
    kredit_slot.metric("Kredit", kredit)
