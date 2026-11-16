import streamlit as st

from katalogin.config import PLATFORMS
from katalogin.web.tampilan import hitung_karakter, tags_ke_teks


def tampilkan_hasil(hasil: dict) -> None:
    platform = hasil["platform"]
    judul_maks = int(PLATFORMS[platform]["judul_maks"])

    st.markdown(f"**{hasil['nama_produk']}**")
    for nomor, judul in enumerate(hasil["judul"], start=1):
        st.caption(f"Judul {nomor} ({hitung_karakter(judul, judul_maks)})")
        st.code(judul, language=None)

    st.caption("Deskripsi")
    st.code(hasil["deskripsi"], language=None)
    st.caption("Tag")
    st.code(tags_ke_teks(hasil["tags"]), language=None)

    if hasil["pelanggaran"]:
        st.warning("Kata terlarang dibersihkan: " + ", ".join(hasil["pelanggaran"]))
