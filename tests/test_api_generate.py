from katalogin import db
from katalogin.api import create_app


TEKS_PRODUK = """KAOS POLOS PRIA
Brand: Oneck
bhn: ktn combed 30s
uk: L
wrn: htm
kegunaan: harian
keunggulan: adem, tidak mudah luntur"""

JUDUL_DIHARAPKAN = [
    "Oneck Kaos Polos Pria Katun Combed 30s L",
    "Kaos Polos Pria Oneck Hitam Katun Combed 30s",
    "Oneck Kaos Polos Pria Hitam L Adem",
]


def test_create_app_menginisialisasi_database_sekali_saat_dibuat(
    monkeypatch, tmp_path
) -> None:
    jalur = str(tmp_path / "katalogin.db")
    panggilan = []

    monkeypatch.setattr(db, "init_db", lambda db_path: panggilan.append(db_path))

    create_app(db_path=jalur)

    assert panggilan == [jalur]


def test_kredit_pengguna_baru_memberikan_lima_kredit(klien) -> None:
    respons = klien.get("/kredit", headers={"X-User-Id": "andi"})

    assert respons.status_code == 200
    assert respons.json() == {"user_id": "andi", "kredit": 5}


def test_kredit_tanpa_header_mengembalikan_401(klien) -> None:
    respons = klien.get("/kredit")

    assert respons.status_code == 401
    assert respons.json() == {"detail": "Header X-User-Id wajib diisi"}


def test_kredit_dengan_user_id_tidak_valid_mengembalikan_400(klien) -> None:
    respons = klien.get("/kredit", headers={"X-User-Id": "a b"})

    assert respons.status_code == 400
    assert respons.json() == {"detail": "X-User-Id tidak valid"}


def test_generate_dari_produk_mengurangi_kredit_dan_mengembalikan_hasil(
    klien, produk_kaos
) -> None:
    respons = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "produk": produk_kaos},
    )

    assert respons.status_code == 200
    assert respons.json()["id"] == 1
    assert respons.json()["sisa_kredit"] == 4
    assert respons.json()["hasil"]["judul"] == JUDUL_DIHARAPKAN
    assert respons.json()["hasil"]["tone"] == "kasual"
    assert klien.get(
        "/kredit", headers={"X-User-Id": "andi"}
    ).json()["kredit"] == 4


def test_generate_dari_teks_menghasilkan_judul_yang_sama(klien) -> None:
    respons = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "tone": "kasual", "teks": TEKS_PRODUK},
    )

    assert respons.status_code == 200
    assert respons.json()["hasil"]["judul"] == JUDUL_DIHARAPKAN
    assert respons.json()["sisa_kredit"] == 4


def test_generate_menuntut_produk_atau_teks_tepat_satu(klien, produk_kaos) -> None:
    respons_keduanya = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={
            "platform": "shopee",
            "produk": produk_kaos,
            "teks": TEKS_PRODUK,
        },
    )
    respons_tidak_satu = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee"},
    )

    assert respons_keduanya.status_code == 400
    assert respons_keduanya.json() == {
        "detail": "Isi tepat salah satu dari 'produk' atau 'teks'"
    }
    assert respons_tidak_satu.status_code == 400
    assert respons_tidak_satu.json() == {
        "detail": "Isi tepat salah satu dari 'produk' atau 'teks'"
    }


def test_generate_dengan_nama_kosong_mengembalikan_400_tanpa_mengubah_kredit(
    klien
) -> None:
    respons = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "produk": {"nama": "   "}},
    )

    assert respons.status_code == 400
    assert respons.json() == {"detail": "Nama produk wajib diisi"}
    assert klien.get(
        "/kredit", headers={"X-User-Id": "andi"}
    ).json()["kredit"] == 5


def test_generate_dengan_platform_tidak_dikenal_mengembalikan_400(
    klien, produk_kaos
) -> None:
    respons = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={"platform": "lazada", "produk": produk_kaos},
    )

    assert respons.status_code == 400
    assert respons.json() == {
        "detail": "Platform tidak dikenal: lazada. Pilihan: shopee, tokopedia, tiktok"
    }
    assert klien.get(
        "/kredit", headers={"X-User-Id": "andi"}
    ).json()["kredit"] == 5


def test_generate_keenam_setelah_lima_kredit_mengembalikan_402(
    klien, produk_kaos
) -> None:
    for sisa_diharapkan in (4, 3, 2, 1, 0):
        respons = klien.post(
            "/generate",
            headers={"X-User-Id": "andi"},
            json={"platform": "shopee", "produk": produk_kaos},
        )

        assert respons.status_code == 200
        assert respons.json()["sisa_kredit"] == sisa_diharapkan

    respons = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "produk": produk_kaos},
    )

    assert respons.status_code == 402
    assert respons.json() == {
        "detail": "Kredit tidak cukup: butuh 1, tersisa 0"
    }
