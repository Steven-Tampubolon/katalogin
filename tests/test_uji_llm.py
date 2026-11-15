from katalogin.llm import FakeLLM, LLMError
from katalogin.uji_llm import main


def test_main_tanpa_klien_menampilkan_galat_kunci(capsys) -> None:
    kode = main([], env={}, buat_klien=lambda env: None)

    tangkap = capsys.readouterr()
    assert kode == 1
    assert tangkap.out == ""
    assert tangkap.err == "GALAT: GEMINI_API_KEY belum diisi\n"


def test_main_teks_memanggil_klien_dan_mencetak_balasan(capsys) -> None:
    llm = FakeLLM("  Halo  ")
    env = {"KATALOGIN_LLM_MODEL": "model-uji"}

    kode = main([], env=env, buat_klien=lambda env: llm)

    tangkap = capsys.readouterr()
    assert kode == 0
    assert tangkap.err == ""
    assert "Balasan AI: Halo" in tangkap.out
    assert llm.prompts == ["Jawab satu kata: halo"]


def test_main_foto_mengirim_gambar_dan_mencetak_balasan(
    capsys, tmp_path, gambar_png
) -> None:
    llm = FakeLLM("Seekor kucing")
    jalur = tmp_path / "gambar.png"
    jalur.write_bytes(gambar_png)

    kode = main(["--foto", str(jalur)], env={}, buat_klien=lambda env: llm)

    tangkap = capsys.readouterr()
    assert kode == 0
    assert tangkap.err == ""
    assert "Balasan AI: Seekor kucing" in tangkap.out
    assert llm.gambar == [
        (
            "Sebutkan benda utama pada gambar ini dalam satu kalimat.",
            gambar_png,
            "image/png",
        )
    ]


def test_main_foto_berkas_tidak_ada_menampilkan_galat(capsys, tmp_path) -> None:
    jalur = tmp_path / "hilang.png"

    kode = main(["--foto", str(jalur)], env={}, buat_klien=lambda env: FakeLLM("x"))

    tangkap = capsys.readouterr()
    assert kode == 1
    assert tangkap.out == ""
    assert tangkap.err == f"GALAT: Berkas tidak ditemukan: {jalur}\n"


def test_main_foto_format_tidak_didukung_menampilkan_galat(capsys, tmp_path) -> None:
    jalur = tmp_path / "gambar.gif"
    jalur.write_bytes(b"GIF89a")

    kode = main(["--foto", str(jalur)], env={}, buat_klien=lambda env: FakeLLM("x"))

    tangkap = capsys.readouterr()
    assert kode == 1
    assert tangkap.out == ""
    assert "GALAT: Format gambar tidak didukung (JPEG, PNG, atau WebP)" in tangkap.err


def test_main_llm_error_menampilkan_galat(capsys) -> None:
    kode = main(
        [],
        env={},
        buat_klien=lambda env: FakeLLM(LLMError("kuota habis")),
    )

    tangkap = capsys.readouterr()
    assert kode == 1
    assert tangkap.out == ""
    assert tangkap.err == "GALAT: kuota habis\n"
