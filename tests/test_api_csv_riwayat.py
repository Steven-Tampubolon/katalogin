import csv
from io import StringIO

from katalogin import db


CSV_DUA_PRODUK = "nama,merek\nKaos,Oneck\nTas,Bagus"
CSV_SATU_PRODUK = "nama,merek\nKaos Polos Pria,Oneck"


def test_generate_csv_mengembalikan_id_hasil_dan_ekspor_csv(klien) -> None:
    respons = klien.post(
        "/generate/csv",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "csv": CSV_DUA_PRODUK},
    )

    assert respons.status_code == 200
    data = respons.json()
    assert len(data["ids"]) == 2
    assert len(data["hasil"]) == 2
    assert data["sisa_kredit"] == 3
    assert data["csv"].splitlines()[0] == (
        "nama_produk,platform,tone,judul_1,judul_2,judul_3,deskripsi,tags,peringatan"
    )
    assert len(list(csv.reader(StringIO(data["csv"])))) == 3


def test_generate_csv_menolak_lebih_dari_20_baris_tanpa_mengubah_kredit(
    klien,
) -> None:
    csv_terlalu_banyak = "nama\n" + "".join(
        f"Produk {nomor}\n" for nomor in range(1, 22)
    )

    respons = klien.post(
        "/generate/csv",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "csv": csv_terlalu_banyak},
    )

    assert respons.status_code == 400
    assert respons.json() == {"detail": "Maksimum 20 baris, ditemukan 21"}
    assert klien.get(
        "/kredit", headers={"X-User-Id": "andi"}
    ).json()["kredit"] == 5


def test_generate_csv_tidak_memproses_saat_kredit_tidak_cukup(klien) -> None:
    csv_enam_produk = "nama\n" + "".join(
        f"Produk {nomor}\n" for nomor in range(1, 7)
    )

    respons = klien.post(
        "/generate/csv",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "csv": csv_enam_produk},
    )

    assert respons.status_code == 402
    assert respons.json() == {
        "detail": "Kredit tidak cukup: butuh 6, tersisa 5"
    }
    assert klien.get(
        "/riwayat", headers={"X-User-Id": "andi"}
    ).json()["total"] == 0
    assert klien.get(
        "/kredit", headers={"X-User-Id": "andi"}
    ).json()["kredit"] == 5


def test_generate_csv_menolak_csv_tanpa_kolom_nama(klien) -> None:
    respons = klien.post(
        "/generate/csv",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "csv": "merek\nOneck"},
    )

    assert respons.status_code == 400
    assert respons.json() == {"detail": "Kolom 'nama' wajib ada"}


def test_generate_csv_menolak_platform_tidak_dikenal(klien) -> None:
    respons = klien.post(
        "/generate/csv",
        headers={"X-User-Id": "andi"},
        json={"platform": "lazada", "csv": CSV_SATU_PRODUK},
    )

    assert respons.status_code == 400
    assert respons.json() == {
        "detail": "Platform tidak dikenal: lazada. Pilihan: shopee, tokopedia, tiktok"
    }
    assert klien.get(
        "/kredit", headers={"X-User-Id": "andi"}
    ).json()["kredit"] == 5


def test_riwayat_menampilkan_total_dan_item_terbaru(klien, produk_kaos) -> None:
    for _ in range(3):
        respons = klien.post(
            "/generate",
            headers={"X-User-Id": "andi"},
            json={"platform": "shopee", "produk": produk_kaos},
        )
        assert respons.status_code == 200

    respons = klien.get("/riwayat", headers={"X-User-Id": "andi"})

    assert respons.status_code == 200
    data = respons.json()
    assert data["total"] == 3
    assert [item["id"] for item in data["item"]] == [3, 2, 1]


def test_riwayat_mendukung_limit_dan_offset(klien, produk_kaos) -> None:
    for _ in range(3):
        respons = klien.post(
            "/generate",
            headers={"X-User-Id": "andi"},
            json={"platform": "shopee", "produk": produk_kaos},
        )
        assert respons.status_code == 200

    respons = klien.get(
        "/riwayat", headers={"X-User-Id": "andi"}, params={"limit": 2, "offset": 1}
    )

    assert respons.status_code == 200
    assert [item["id"] for item in respons.json()["item"]] == [2, 1]


def test_riwayat_id_mengembalikan_hasil_lengkap(klien, produk_kaos) -> None:
    for _ in range(3):
        respons = klien.post(
            "/generate",
            headers={"X-User-Id": "andi"},
            json={"platform": "shopee", "produk": produk_kaos},
        )
        assert respons.status_code == 200

    respons = klien.get("/riwayat/2", headers={"X-User-Id": "andi"})

    assert respons.status_code == 200
    assert respons.json()["hasil"]["nama_produk"] == "Kaos Polos Pria"


def test_riwayat_id_milik_pengguna_lain_mengembalikan_404(klien, produk_kaos) -> None:
    respons_generate = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "produk": produk_kaos},
    )
    assert respons_generate.status_code == 200

    respons = klien.get("/riwayat/1", headers={"X-User-Id": "budi"})

    assert respons.status_code == 404
    assert respons.json() == {"detail": "Riwayat tidak ditemukan"}


def test_riwayat_id_yang_tidak_ada_mengembalikan_404(klien) -> None:
    respons = klien.get("/riwayat/999", headers={"X-User-Id": "andi"})

    assert respons.status_code == 404
    assert respons.json() == {"detail": "Riwayat tidak ditemukan"}


def test_riwayat_menolak_limit_dan_offset_di_luar_rentang(klien) -> None:
    respons_limit_nol = klien.get(
        "/riwayat", headers={"X-User-Id": "andi"}, params={"limit": 0}
    )
    respons_limit_terlalu_besar = klien.get(
        "/riwayat", headers={"X-User-Id": "andi"}, params={"limit": 101}
    )
    respons_offset_negatif = klien.get(
        "/riwayat", headers={"X-User-Id": "andi"}, params={"offset": -1}
    )

    assert respons_limit_nol.status_code == 422
    assert respons_limit_terlalu_besar.status_code == 422
    assert respons_offset_negatif.status_code == 422


def test_riwayat_untuk_pengguna_baru_tidak_membuat_pengguna(klien) -> None:
    respons = klien.get("/riwayat", headers={"X-User-Id": "siti"})

    assert respons.status_code == 200
    assert respons.json() == {"total": 0, "item": []}
    koneksi = db.buka(klien.app.state.db_path)
    try:
        jumlah_pengguna = koneksi.execute(
            "SELECT COUNT(*) FROM pengguna WHERE user_id = ?", ("siti",)
        ).fetchone()[0]
    finally:
        koneksi.close()
    assert jumlah_pengguna == 0
