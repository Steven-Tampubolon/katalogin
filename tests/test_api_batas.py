import asyncio
import json
from pathlib import Path

import pytest

from katalogin import credits, db
from katalogin.api import BATAS_CONTENT_LENGTH


AKAR_PROYEK = Path(__file__).resolve().parents[1]


def _assert_tidak_ada_data(klien, user_id: str) -> None:
    koneksi = db.buka(klien.app.state.db_path)
    try:
        jumlah_pengguna = koneksi.execute(
            "SELECT COUNT(*) FROM pengguna WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
        jumlah_ledger = koneksi.execute(
            "SELECT COUNT(*) FROM ledger WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
        jumlah_riwayat = koneksi.execute(
            "SELECT COUNT(*) FROM riwayat WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
    finally:
        koneksi.close()

    assert jumlah_pengguna == 0
    assert jumlah_ledger == 0
    assert jumlah_riwayat == 0


def _jalankan_asgi_chunked(app, chunks: list[bytes]) -> tuple[int, bytes, int]:
    status_kode: int | None = None
    bagian_body: list[bytes] = []
    jumlah_diterima = 0

    async def receive():
        nonlocal jumlah_diterima
        if not chunks:
            return {"type": "http.disconnect"}
        chunk = chunks.pop(0)
        jumlah_diterima += len(chunk)
        return {
            "type": "http.request",
            "body": chunk,
            "more_body": bool(chunks),
        }

    async def send(message) -> None:
        nonlocal status_kode
        if message["type"] == "http.response.start":
            status_kode = message["status"]
        elif message["type"] == "http.response.body":
            bagian_body.append(message.get("body", b""))

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/generate",
        "raw_path": b"/generate",
        "query_string": b"",
        "root_path": "",
        "headers": [
            (b"host", b"testserver"),
            (b"content-type", b"application/json"),
            (b"transfer-encoding", b"chunked"),
            (b"x-user-id", b"andi"),
        ],
        "klient": ("testklient", 50000),
        "server": ("testserver", 80),
        "state": {},
    }

    asyncio.run(app(scope, receive, send))

    assert status_kode is not None
    return status_kode, b"".join(bagian_body), jumlah_diterima


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


@pytest.mark.parametrize(
    ("jalur", "muatan"),
    [
        (
            "/generate",
            {
                "platform": "shopee" + " " * 24,
                "produk": {"nama": "Kaos"},
            },
        ),
        (
            "/generate",
            {
                "platform": "shopee",
                "tone": "kasual" + " " * 24,
                "produk": {"nama": "Kaos"},
            },
        ),
        (
            "/generate/csv",
            {"platform": "shopee" + " " * 24, "csv": "nama\nKaos"},
        ),
        (
            "/generate/csv",
            {
                "platform": "shopee",
                "tone": "kasual" + " " * 24,
                "csv": "nama\nKaos",
            },
        ),
    ],
)
def test_platform_dan_tone_tepat_30_karakter_diterima(
    klien, jalur, muatan
) -> None:
    respons = klien.post(
        jalur,
        headers={"X-User-Id": "andi"},
        json=muatan,
    )

    assert respons.status_code == 200


def test_generate_csv_menolak_csv_lebih_dari_100000_karakter(klien) -> None:
    respons = klien.post(
        "/generate/csv",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "csv": "a" * 100001},
    )

    assert respons.status_code == 422


def test_generate_csv_menerima_csv_tepat_100000_karakter(klien) -> None:
    csv_valid = "nama\nKaos\n"
    csv_valid += " " * (100000 - len(csv_valid))

    respons = klien.post(
        "/generate/csv",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "csv": csv_valid},
    )

    assert len(csv_valid) == 100000
    assert respons.status_code == 200


def test_admin_kredit_menolak_user_id_lebih_dari_64_karakter(klien) -> None:
    respons = klien.post(
        "/admin/kredit",
        headers={"X-Admin-Token": "token-uji"},
        json={"user_id": "a" * 65, "jumlah": 10},
    )

    assert respons.status_code == 422


def test_admin_kredit_menerima_user_id_tepat_64_karakter(klien) -> None:
    user_id = "a" * 64
    koneksi = db.buka(klien.app.state.db_path)
    try:
        with db.transaksi(koneksi):
            waktu = db.sekarang()
            credits.pastikan_pengguna(koneksi, user_id, waktu)
            credits.kurangi(
                koneksi, user_id, credits.KREDIT_GRATIS, "penggunaan", waktu
            )
    finally:
        koneksi.close()

    respons = klien.post(
        "/admin/kredit",
        headers={"X-Admin-Token": "token-uji"},
        json={"user_id": user_id, "jumlah": 10},
    )

    assert respons.status_code == 200
    assert respons.json() == {"user_id": user_id, "kredit": 10}


def test_teks_900000_karakter_ditolak_dan_tidak_menulis_data(klien) -> None:
    respons = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "teks": "a" * 900000},
    )

    assert respons.status_code == 422
    _assert_tidak_ada_data(klien, "andi")


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
    _assert_tidak_ada_data(klien, "budi")


def test_permintaan_chunked_tanpa_content_length_dibatasi_ke_1_juta_byte(
    klien,
) -> None:
    prefix = b'{"platform":"shopee","teks":"'
    chunks = [
        prefix,
        b"a" * (BATAS_CONTENT_LENGTH - len(prefix)),
        b"a" * 10000,
        b'"}',
    ]
    panjang_body = sum(len(chunk) for chunk in chunks)

    status_kode, body, jumlah_diterima = _jalankan_asgi_chunked(klien.app, chunks)

    assert status_kode == 413
    assert json.loads(body) == {"detail": "Permintaan terlalu besar"}
    assert jumlah_diterima < panjang_body
    _assert_tidak_ada_data(klien, "andi")


def test_permintaan_chunked_dalam_batas_diproses(klien) -> None:
    chunks = [b'{"platform":"shopee","produk":{"nama":"Kaos"}}']
    panjang_body = sum(len(chunk) for chunk in chunks)

    status_kode, _, jumlah_diterima = _jalankan_asgi_chunked(klien.app, chunks)

    assert status_kode == 200
    assert jumlah_diterima == panjang_body


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
    isi_readme = (AKAR_PROYEK / "README.md").read_text(encoding="utf-8")

    assert "Batas masukan" in isi_readme
    assert "413" in isi_readme
    assert "20000" in isi_readme
    assert "100000" in isi_readme
