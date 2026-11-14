import csv
from io import StringIO

from katalogin.models import Product
from katalogin.pipeline import Hasil
from katalogin.textutil import rapikan_spasi, rapikan_teks

_KOLOM_PRODUK = ("nama", "merek", "bahan", "ukuran", "warna", "fungsi", "fitur")
_HEADER_HASIL = (
    "nama_produk",
    "platform",
    "tone",
    "judul_1",
    "judul_2",
    "judul_3",
    "deskripsi",
    "tags",
    "peringatan",
)


def _pilih_delimiter(baris_pertama: str) -> str:
    return ";" if baris_pertama.count(";") > baris_pertama.count(",") else ","


def _nilai(baris: list[str], indeks: dict[str, int], kolom: str) -> str:
    posisi = indeks.get(kolom)
    if posisi is None or posisi >= len(baris):
        return ""
    return baris[posisi]


def _nilai_opsional(
    baris: list[str], indeks: dict[str, int], kolom: str, perakit
) -> str | None:
    mentah = _nilai(baris, indeks, kolom)
    if not mentah.strip():
        return None
    nilai = perakit(mentah)
    return nilai or None


def _buat_produk(baris: list[str], indeks: dict[str, int]) -> Product:
    nama = rapikan_teks(_nilai(baris, indeks, "nama"))
    if not nama:
        raise ValueError("Kolom 'nama' kosong")

    fitur = [
        rapikan_teks(item.strip())
        for item in _nilai(baris, indeks, "fitur").split("|")
        if item.strip()
    ]

    return Product(
        nama=nama,
        merek=_nilai_opsional(baris, indeks, "merek", rapikan_spasi),
        bahan=_nilai_opsional(baris, indeks, "bahan", rapikan_teks),
        ukuran=_nilai_opsional(baris, indeks, "ukuran", rapikan_teks),
        warna=_nilai_opsional(baris, indeks, "warna", rapikan_teks),
        fungsi=_nilai_opsional(baris, indeks, "fungsi", rapikan_teks),
        fitur=fitur,
    )


def baca_csv(teks: str) -> list[Product]:
    teks = teks.removeprefix("\ufeff")
    if not teks.strip():
        raise ValueError("CSV kosong")

    delimiter = _pilih_delimiter(teks.splitlines()[0])
    semua_baris = list(csv.reader(StringIO(teks, newline=""), delimiter=delimiter))
    header = semua_baris[0]
    indeks = {
        nama.strip().lower(): posisi
        for posisi, nama in enumerate(header)
        if nama.strip().lower() in _KOLOM_PRODUK
    }
    if "nama" not in indeks:
        raise ValueError("Kolom 'nama' wajib ada")

    baris_data = [
        (nomor, baris)
        for nomor, baris in enumerate(semua_baris[1:], start=2)
        if any(sel.strip() for sel in baris)
    ]
    if len(baris_data) > 20:
        raise ValueError(f"Maksimum 20 baris, ditemukan {len(baris_data)}")

    daftar_produk = []
    for nomor, baris in baris_data:
        if not rapikan_teks(_nilai(baris, indeks, "nama")):
            raise ValueError(f"Baris {nomor}: kolom 'nama' kosong")
        daftar_produk.append(_buat_produk(baris, indeks))

    return daftar_produk


def ekspor_csv(daftar_hasil: list[Hasil]) -> str:
    keluaran = StringIO(newline="")
    penulis = csv.writer(keluaran, lineterminator="\n")
    penulis.writerow(_HEADER_HASIL)

    for hasil in daftar_hasil:
        judul = list(hasil.judul[:3])
        judul.extend([""] * (3 - len(judul)))
        penulis.writerow(
            [
                hasil.nama_produk,
                hasil.platform,
                hasil.tone,
                *judul,
                hasil.deskripsi,
                ", ".join(hasil.tags),
                "; ".join(hasil.pelanggaran),
            ]
        )

    return keluaran.getvalue()
