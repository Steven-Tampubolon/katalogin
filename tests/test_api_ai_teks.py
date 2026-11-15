import pytest

from katalogin.llm import FakeLLM


TEKS_AI = "kaos oneck hitam"
TEKS_ATURAN = "KAOS POLOS PRIA\nwrn: htm"
JUDUL_DIHARAPKAN = [
    "Oneck Kaos Polos Pria Katun Combed 30s L",
    "Kaos Polos Pria Oneck Hitam Katun Combed 30s",
    "Oneck Kaos Polos Pria Hitam L Adem",
]


def test_generate_dengan_ai_memakai_hasil_llm(
    buat_klien_ai, json_kaos
) -> None:
    llm = FakeLLM(json_kaos)
    klien = buat_klien_ai(llm)

    respons = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "teks": TEKS_AI, "gunakan_ai": True},
    )

    assert respons.status_code == 200
    data = respons.json()
    assert data["ekstraksi"] == "ai"
    assert data["hasil"]["judul"] == JUDUL_DIHARAPKAN
    assert data["sisa_kredit"] == 4
    assert TEKS_AI in llm.prompts[0]


@pytest.mark.parametrize("respons", ["bukan json", RuntimeError("x")])
def test_generate_dengan_ai_jatuh_ke_aturan_bila_llm_gagal(
    buat_klien_ai, respons
) -> None:
    llm = FakeLLM(respons)
    klien = buat_klien_ai(llm)

    hasil = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "teks": TEKS_ATURAN, "gunakan_ai": True},
    )

    assert hasil.status_code == 200
    assert hasil.json()["ekstraksi"] == "aturan"
    assert hasil.json()["hasil"]["nama_produk"] == "Kaos Polos Pria"
    assert len(llm.prompts) == 1


def test_generate_dengan_ai_mengembalikan_400_bila_aturan_tidak_menemukan_nama(
    buat_klien_ai,
) -> None:
    llm = FakeLLM("bukan json")
    klien = buat_klien_ai(llm)

    respons = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "teks": "merek: Oneck", "gunakan_ai": True},
    )

    assert respons.status_code == 400
    assert respons.json() == {"detail": "Nama produk tidak ditemukan"}
    assert len(llm.prompts) == 1


def test_generate_dengan_ai_menolak_produk(buat_klien_ai, produk_kaos) -> None:
    llm = FakeLLM("x")
    klien = buat_klien_ai(llm)

    respons = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={
            "platform": "shopee",
            "produk": produk_kaos,
            "gunakan_ai": True,
        },
    )

    assert respons.status_code == 400
    assert respons.json() == {
        "detail": "gunakan_ai hanya berlaku untuk 'teks'"
    }
    assert llm.prompts == []


def test_generate_dengan_ai_tanpa_klien_mengembalikan_503_dan_tidak_mengubah_kredit(
    klien,
) -> None:
    respons = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "teks": TEKS_AI, "gunakan_ai": True},
    )

    assert respons.status_code == 503
    assert respons.json() == {"detail": "Layanan AI belum dikonfigurasi"}
    assert klien.get(
        "/kredit", headers={"X-User-Id": "andi"}
    ).json()["kredit"] == 5


def test_generate_tanpa_gunakan_ai_tidak_memanggil_llm_dan_tidak_menambah_ekstraksi(
    buat_klien_ai, json_kaos, produk_kaos
) -> None:
    llm = FakeLLM(json_kaos)
    klien = buat_klien_ai(llm)

    respons = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "produk": produk_kaos},
    )

    assert respons.status_code == 200
    assert "ekstraksi" not in respons.json()
    assert llm.prompts == []


def test_generate_dengan_ai_menolak_kredit_kosong_sebelum_memanggil_llm(
    buat_klien_ai, json_kaos, produk_kaos
) -> None:
    llm = FakeLLM(json_kaos)
    klien = buat_klien_ai(llm)

    for _ in range(5):
        respons = klien.post(
            "/generate",
            headers={"X-User-Id": "andi"},
            json={"platform": "shopee", "produk": produk_kaos},
        )
        assert respons.status_code == 200

    respons = klien.post(
        "/generate",
        headers={"X-User-Id": "andi"},
        json={"platform": "shopee", "teks": TEKS_AI, "gunakan_ai": True},
    )

    assert respons.status_code == 402
    assert respons.json() == {
        "detail": "Kredit tidak cukup: butuh 1, tersisa 0"
    }
    assert llm.prompts == []
