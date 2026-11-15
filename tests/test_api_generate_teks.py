TEKS_PRODUK = """KAOS POLOS PRIA
Brand: Oneck
bhn: ktn combed 30s
uk: L
wrn: htm
kegunaan: harian
keunggulan: adem, tidak mudah luntur"""


def test_generate_dari_teks_tanpa_nama_produk_mengembalikan_400(
    klien,
) -> None:
    for teks in ("merek: Oneck", "", "   \n  "):
        respons = klien.post(
            "/generate",
            headers={"X-User-Id": "andi"},
            json={"platform": "shopee", "teks": teks},
        )

        assert respons.status_code == 400
        assert respons.json() == {"detail": "Nama produk tidak ditemukan"}

    respons_kredit = klien.get("/kredit", headers={"X-User-Id": "andi"})
    respons_riwayat = klien.get("/riwayat", headers={"X-User-Id": "andi"})

    assert respons_kredit.json() == {"user_id": "andi", "kredit": 5}
    assert respons_riwayat.json()["total"] == 0


def test_generate_dari_teks_valid_tetap_menghasilkan_judul(klien) -> None:
    respons = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "teks": TEKS_PRODUK},
    )

    assert respons.status_code == 200
    assert respons.json()["hasil"]["judul"][0] == (
        "Oneck Kaos Polos Pria Katun Combed 30s L"
    )
