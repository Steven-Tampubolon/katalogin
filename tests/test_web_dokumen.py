from pathlib import Path

import tomllib


AKAR_REPO = Path(__file__).resolve().parents[1]


def test_konfigurasi_streamlit_menonaktifkan_telemetri_dan_membatasi_unggah() -> None:
    with (AKAR_REPO / ".streamlit" / "config.toml").open("rb") as berkas:
        konfigurasi = tomllib.load(berkas)

    assert konfigurasi["browser"]["gatherUsageStats"] is False
    assert konfigurasi["server"]["maxUploadSize"] == 6


def test_readme_mendokumentasikan_antarmuka_web_dan_konfigurasi_ai() -> None:
    isi_readme = (AKAR_REPO / "README.md").read_text(encoding="utf-8")

    assert "Antarmuka web" in isi_readme
    assert "streamlit run katalogin/web/app.py" in isi_readme
    assert "uvicorn katalogin.main:app" in isi_readme
    assert "KATALOGIN_API_URL" in isi_readme
    assert "ID pengguna" in isi_readme
    assert "konfigurasi AI" in isi_readme


def test_requirements_memuat_streamlit() -> None:
    isi_requirements = (AKAR_REPO / "requirements.txt").read_text(encoding="utf-8")

    assert "streamlit>=1.40" in isi_requirements.splitlines()
