import sys
from pathlib import Path


AKAR_REPO = Path(__file__).resolve().parents[2]
if str(AKAR_REPO) not in sys.path:
    sys.path.insert(0, str(AKAR_REPO))

import streamlit as st

from katalogin.web.komponen import tampilkan_hasil
from katalogin.web.klien_api import ApiError, KlienApi, buat_http_dari_env
from katalogin.web.tampilan import PLATFORM_OPSI, TONE_OPSI, pesan_galat


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

try:
    kredit = api.kredit()
except ApiError as galat:
    kredit_slot.error(pesan_galat(galat))
else:
    kredit_slot.metric("Kredit", kredit)
