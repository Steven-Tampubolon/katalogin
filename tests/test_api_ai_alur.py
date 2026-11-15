import base64
from pathlib import Path

from katalogin.llm import FakeLLM


AKAR_PROYEK = Path(__file__).resolve().parents[1]
JUDUL_DIHARAPKAN = [
    "Oneck Kaos Polos Pria Katun Combed 30s L",
    "Kaos Polos Pria Oneck Hitam Katun Combed 30s",
    "Oneck Kaos Polos Pria Hitam L Adem",
]


def test_alur_foto_teks_ai_dan_produk_menggunakan_satu_kredit(
    buat_klien_ai, json_kaos, produk_kaos, gambar_png
) -> None:
    llm = FakeLLM(json_kaos)
    klien = buat_klien_ai(llm)
    gambar_base64 = base64.b64encode(gambar_png).decode("ascii")
    permintaan = [
        (
            "/generate/foto",
            {"platform": "shopee", "gambar_base64": gambar_base64},
        ),
        (
            "/generate",
            {
                "platform": "shopee",
                "teks": "kaos oneck hitam",
                "gunakan_ai": True,
            },
        ),
        (
            "/generate",
            {"platform": "shopee", "produk": produk_kaos},
        ),
    ]

    respons = [
        klien.post(
            jalur,
            headers={"X-User-Id": "andi"},
            json=muatan,
        )
        for jalur, muatan in permintaan
    ]

    assert [item.status_code for item in respons] == [200, 200, 200]
    assert [item.json()["hasil"]["judul"] for item in respons] == [
        JUDUL_DIHARAPKAN,
        JUDUL_DIHARAPKAN,
        JUDUL_DIHARAPKAN,
    ]
    assert [item.json()["sisa_kredit"] for item in respons] == [4, 3, 2]

    riwayat = klien.get("/riwayat", headers={"X-User-Id": "andi"})
    assert riwayat.status_code == 200
    assert riwayat.json()["total"] == 3
    assert [item["id"] for item in riwayat.json()["item"]] == [3, 2, 1]
    assert len(llm.gambar) == 1
    assert len(llm.prompts) == 1


def test_readme_mendokumentasikan_konfigurasi_dan_alur_ai() -> None:
    isi_readme = (AKAR_PROYEK / "README.md").read_text(encoding="utf-8")

    for isi_wajib in (
        "GEMINI_API_KEY",
        "KATALOGIN_LLM_MODEL",
        "/generate/foto",
        "gunakan_ai",
        "python -m katalogin.uji_llm",
        "502",
        "503",
    ):
        assert isi_wajib in isi_readme
