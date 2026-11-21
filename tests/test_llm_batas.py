import json
import pytest

from katalogin.extract import ekstrak_teks
from katalogin.llm import (
    BATAS_FIELD,
    BATAS_FITUR_JUMLAH,
    BATAS_FITUR_PANJANG,
    FakeLLM,
    coba_ekstrak_dengan_llm_rinci,
    ekstrak_dengan_llm,
    ekstrak_dari_gambar,
)
from katalogin.models import Product


def _make_json(**kwargs) -> str:
    return json.dumps(kwargs)


def test_batas_field_didefinisikan() -> None:
    assert BATAS_FIELD == 200
    assert BATAS_FITUR_JUMLAH == 20
    assert BATAS_FITUR_PANJANG == 100


def test_nama_200_karakter_diterima() -> None:
    client = FakeLLM(_make_json(nama="x" * 200, merek="Oneck", fitur=["f1"]))
    produk = ekstrak_dengan_llm("teks", client)
    assert produk is not None
    assert len(produk.nama) == 200


def test_nama_201_karakter_hasil_none_coba_llm() -> None:
    client = FakeLLM(_make_json(nama="x" * 201, merek="Oneck", fitur=["f1"]))
    produk, alasan = coba_ekstrak_dengan_llm_rinci("teks", client)
    assert produk is None
    assert alasan == "respons_tidak_valid"


def test_mereka_201_karakter_jadi_none() -> None:
    client = FakeLLM(_make_json(nama="Kaos", merek="x" * 201, fitur=["f1"]))
    produk = ekstrak_dengan_llm("teks", client)
    assert produk is not None
    assert produk.merek is None
    assert produk.nama == "Kaos"


def test_bahan_201_karakter_jadi_none() -> None:
    client = FakeLLM(_make_json(nama="Kaos", bahan="x" * 201, fitur=["f1"]))
    produk = ekstrak_dengan_llm("teks", client)
    assert produk is not None
    assert produk.bahan is None
    assert produk.nama == "Kaos"


def test_ukuran_201_karakter_jadi_none() -> None:
    client = FakeLLM(_make_json(nama="Kaos", ukuran="x" * 201, fitur=["f1"]))
    produk = ekstrak_dengan_llm("teks", client)
    assert produk is not None
    assert produk.ukuran is None
    assert produk.nama == "Kaos"


def test_warna_201_karakter_jadi_none() -> None:
    client = FakeLLM(_make_json(nama="Kaos", warna="x" * 201, fitur=["f1"]))
    produk = ekstrak_dengan_llm("teks", client)
    assert produk is not None
    assert produk.warna is None
    assert produk.nama == "Kaos"


def test_fungsi_201_karakter_jadi_none() -> None:
    client = FakeLLM(_make_json(nama="Kaos", fungsi="x" * 201, fitur=["f1"]))
    produk = ekstrak_dengan_llm("teks", client)
    assert produk is not None
    assert produk.fungsi is None
    assert produk.nama == "Kaos"


def test_fitur_25_item_hasil_20() -> None:
    fitur = ["f" + str(i) for i in range(1, 26)]
    client = FakeLLM(_make_json(nama="Kaos", merek="Oneck", fitur=fitur))
    produk = ekstrak_dengan_llm("teks", client)
    assert produk is not None
    assert produk.fitur == ["f" + str(i) for i in range(1, 21)]


def test_fitur_panjang_dibuat_ambil_20() -> None:
    client = FakeLLM(_make_json(nama="Kaos", merek="Oneck", fitur=["adem", "z" * 101, "z" * 100, "nyaman"]))
    produk = ekstrak_dengan_llm("teks", client)
    assert produk is not None
    assert produk.fitur == ["Adem", "Z" + "z" * 99, "Nyaman"]


def test_fitur_satu_panjang_depan_lain_20() -> None:
    fitur = ["z" * 101] + ["f" + str(i) for i in range(1, 22)]
    client = FakeLLM(_make_json(nama="Kaos", merek="Oneck", fitur=fitur))
    produk = ekstrak_dengan_llm("teks", client)
    assert produk is not None
    expected = ["f" + str(i) for i in range(1, 21)]
    assert produk.fitur == expected


def test_ekstrak_dari_gambar_nama_201_melempar_value_error() -> None:
    client = FakeLLM(_make_json(nama="x" * 201, merek="Oneck", fitur=["f1"]))
    with pytest.raises(ValueError, match="^Gagal membaca produk dari gambar$"):
        ekstrak_dari_gambar(b"gambar", "image/png", client)


def test_ekstrak_dari_gambar_warna_201_warna_none() -> None:
    client = FakeLLM(_make_json(nama="Kaos", warna="x" * 201, merek="Oneck", fitur=["f1"]))
    produk = ekstrak_dari_gambar(b"gambar", "image/png", client)
    assert produk is not None
    assert produk.warna is None
    assert produk.nama == "Kaos"


def test_ekstrak_dengan_llm_nama_201_fallback_teks() -> None:
    client = FakeLLM(_make_json(nama="x" * 201, merek="Oneck", fitur=["f1"]))
    assert ekstrak_dengan_llm("KAOS POLOS PRIA\nbhn: ktn", client) == ekstrak_teks("KAOS POLOS PRIA\nbhn: ktn")