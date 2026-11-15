from pathlib import Path

import pytest


def test_produk_menerima_field_teks_200_karakter_dan_menolak_201(
    klien, produk_kaos
) -> None:
    for nama_field in ("nama", "merek", "bahan", "ukuran", "warna", "fungsi"):
        user_id = f"pengguna-{nama_field}"
        produk_valid = {**produk_kaos, nama_field: "A" * 200}
        respons_valid = klien.post(
            "/generate",
            headers={"X-User-Id": user_id},
            json={"platform": "shopee", "produk": produk_valid},
        )

        produk_terlalu_besar = {**produk_kaos, nama_field: "A" * 201}
        respons_terlalu_besar = klien.post(
            "/generate",
            headers={"X-User-Id": user_id},
            json={"platform": "shopee", "produk": produk_terlalu_besar},
        )

        assert respons_valid.status_code == 200
        assert respons_terlalu_besar.status_code == 422


def test_produk_menerima_20_fitur_dan_menolak_21_fitur(klien, produk_kaos) -> None:
    produk_valid = {**produk_kaos, "fitur": ["fitur"] * 20}
    respons_valid = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "produk": produk_valid},
    )

    produk_terlalu_banyak = {**produk_kaos, "fitur": ["fitur"] * 21}
    respons_terlalu_banyak = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "produk": produk_terlalu_banyak},
    )

    assert respons_valid.status_code == 200
    assert respons_terlalu_banyak.status_code == 422


def test_produk_menerima_item_fitur_100_karakter_dan_menolak_101(
    klien, produk_kaos
) -> None:
    produk_valid = {**produk_kaos, "fitur": ["A" * 100]}
    respons_valid = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "produk": produk_valid},
    )

    produk_terlalu_besar = {**produk_kaos, "fitur": ["A" * 101]}
    respons_terlalu_besar = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "produk": produk_terlalu_besar},
    )

    assert respons_valid.status_code == 200
    assert respons_terlalu_besar.status_code == 422


def test_generate_menerima_teks_20000_karakter_dan_menolak_20001(
    klien,
) -> None:
    respons_valid = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "teks": "nama: " + "a" * 19994},
    )

    respons_terlalu_besar = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "teks": "nama: " + "a" * 19995},
    )

    assert respons_valid.status_code == 200
    assert respons_terlalu_besar.status_code == 422


@pytest.mark.parametrize(
    ("jalur", "muatan"),
    [
        ("/generate", {"platform": "p" * 31, "produk": {"nama": "Kaos"}}),
        ("/generate", {"platform": "shopee", "tone": "t" * 31, "produk": {"nama": "Kaos"}}),
        ("/generate/csv", {"platform": "p" * 31, "csv": "nama\nKaos"}),
        ("/generate/csv", {"platform": "shopee", "tone": "t" * 31, "csv": "nama\nKaos"}),
    ],
)
def test_platform_dan_tone_maksimal_30_karakter(
    klien, jalur, muatan
) -> None:
    respons = klien.post(
        jalur,
        headers={"X-User-Id": "andi"},
        json=muatan,
    )

    assert respons.status_code == 422


def test_generate_csv_menolak_csv_lebih_dari_100000_karakter(klien) -> None:
    respons = klien.post(
        "/generate/csv",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "csv": "a" * 100001},
    )

    assert respons.status_code == 422


def test_admin_kredit_menolak_user_id_lebih_dari_64_karakter(klien) -> None:
    respons = klien.post(
        "/admin/kredit",
        headers={"X-Admin-Token": "token-uji"},
        json={"user_id": "a" * 65, "jumlah": 10},
    )

    assert respons.status_code == 422


def test_teks_900000_karakter_ditolak_dan_tidak_menulis_data(klien) -> None:
    respons = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "teks": "a" * 900000},
    )

    assert respons.status_code == 422
    assert klien.get(
        "/kredit", headers={"X-User-Id": "andi"}
    ).json()["kredit"] == 5
    assert klien.get(
        "/riwayat", headers={"X-User-Id": "andi"}
    ).json()["total"] == 0


def test_permintaan_generate_di_atas_1_juta_byte_mengembalikan_413(
    klien,
) -> None:
    respons = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "teks": "a" * 2000000},
    )

    assert respons.status_code == 413
    assert respons.json() == {"detail": "Permintaan terlalu besar"}


def test_permintaan_csv_di_atas_1_juta_byte_mengembalikan_413(klien) -> None:
    respons = klien.post(
        "/generate/csv",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "csv": "a" * 1100000},
    )

    assert respons.status_code == 413
    assert respons.json() == {"detail": "Permintaan terlalu besar"}


def test_permintaan_413_tidak_menulis_data(klien) -> None:
    respons = klien.post(
        "/generate",
        headers={"X-User-Id": "budi"},
        json={"platform": "shopee", "teks": "a" * 2000000},
    )

    assert respons.status_code == 413
    assert klien.get(
        "/kredit", headers={"X-User-Id": "budi"}
    ).json()["kredit"] == 5
    assert klien.get(
        "/riwayat", headers={"X-User-Id": "budi"}
    ).json()["total"] == 0


def test_content_length_tidak_ada_atau_bukan_angka_diteruskan(klien) -> None:
    respons_tanpa_header = klien.get("/health")
    respons_bukan_angka = klien.get(
        "/health", headers={"Content-Length": "bukan-angka"}
    )

    assert respons_tanpa_header.status_code == 200
    assert respons_bukan_angka.status_code == 200


def test_health_tetap_berfungsi(klien) -> None:
    respons = klien.get("/health")

    assert respons.status_code == 200
    assert respons.json() == {"status": "ok"}


def test_readme_mendokumentasikan_batas_masukan() -> None:
    isi_readme = Path("README.md").read_text(encoding="utf-8")

    assert "Batas masukan" in isi_readme
    assert "413" in isi_readme
    assert "20000" in isi_readme
    assert "100000" in isi_readme
