from pathlib import Path

from katalogin import db


AKAR_PROYEK = Path(__file__).resolve().parents[1]


def test_alur_lengkap_generate_topup_dan_riwayat(klien, produk_kaos) -> None:
    for sisa_diharapkan in (4, 3, 2, 1, 0):
        respons = klien.post(
            "/generate",
            headers={"X-User-Id": "andi"},
            json={"platform": "shopee", "produk": produk_kaos},
        )

        assert respons.status_code == 200
        assert respons.json()["sisa_kredit"] == sisa_diharapkan

    respons_kurang = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "produk": produk_kaos},
    )

    assert respons_kurang.status_code == 402
    assert respons_kurang.json() == {
        "detail": "Kredit tidak cukup: butuh 1, tersisa 0"
    }

    respons_topup = klien.post(
        "/admin/kredit",
        headers={"X-Admin-Token": "token-uji"},
        json={"user_id": "andi", "jumlah": 10},
    )

    assert respons_topup.status_code == 200
    assert respons_topup.json() == {"user_id": "andi", "kredit": 10}

    respons_setelah_topup = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "produk": produk_kaos},
    )

    assert respons_setelah_topup.status_code == 200
    assert respons_setelah_topup.json()["sisa_kredit"] == 9

    respons_riwayat = klien.get("/riwayat", headers={"X-User-Id": "andi"})

    assert respons_riwayat.status_code == 200
    assert respons_riwayat.json()["total"] == 6

    respons_riwayat_budi = klien.get("/riwayat", headers={"X-User-Id": "budi"})

    assert respons_riwayat_budi.status_code == 200
    assert respons_riwayat_budi.json()["total"] == 0

    koneksi = db.buka(klien.app.state.db_path)
    try:
        jumlah_ledger = koneksi.execute(
            "SELECT SUM(delta) FROM ledger WHERE user_id = ?", ("andi",)
        ).fetchone()[0]
    finally:
        koneksi.close()

    assert jumlah_ledger == 9
    assert klien.get(
        "/kredit", headers={"X-User-Id": "andi"}
    ).json()["kredit"] == 9


def test_readme_memuat_ketujuh_jalur_endpoint() -> None:
    isi_readme = (AKAR_PROYEK / "README.md").read_text()

    for jalur in (
        "/health",
        "/kredit",
        "/generate",
        "/generate/csv",
        "/riwayat",
        "/riwayat/{id}",
        "/admin/kredit",
    ):
        assert jalur in isi_readme


def test_main_menyediakan_aplikasi_tanpa_mengimpornya_dalam_tes() -> None:
    isi_main = (AKAR_PROYEK / "katalogin" / "main.py").read_text()

    assert "from katalogin.api import create_app" in isi_main
    assert "app = create_app()" in isi_main
