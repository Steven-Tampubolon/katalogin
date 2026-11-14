import argparse
import sys

from katalogin.csvio import baca_csv, ekspor_csv
from katalogin.extract import ekstrak_teks
from katalogin.models import Product
from katalogin.pipeline import Hasil, generate_batch

PLATFORM = ("shopee", "tokopedia", "tiktok")
TONE = ("kasual", "profesional", "singkat")


def _buat_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="katalogin",
        description="Ubah teks produk mentah atau CSV menjadi listing marketplace.",
    )
    parser.add_argument(
        "--platform",
        required=True,
        choices=PLATFORM,
        help="Platform marketplace tujuan",
    )
    parser.add_argument(
        "--tone",
        default="kasual",
        choices=TONE,
        help="Tone deskripsi (bawaan: kasual)",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Jalur berkas masukan (.txt atau .csv)",
    )
    parser.add_argument(
        "--out",
        help="Jalur berkas CSV hasil (opsional; tanpa ini cetak ke stdout)",
    )
    return parser


def _baca_produk(jalur: str) -> list[Product]:
    with open(jalur, "r", encoding="utf-8") as berkas:
        teks = berkas.read()
    if jalur.lower().endswith(".csv"):
        return baca_csv(teks)
    return [ekstrak_teks(teks)]


def _format_hasil(hasil: Hasil) -> str:
    baris: list[str] = [
        f"== {hasil.nama_produk} ==",
        f"Platform: {hasil.platform} | Tone: {hasil.tone}",
    ]
    for nomor, judul in enumerate(hasil.judul[:3], start=1):
        baris.append(f"Judul {nomor}: {judul}")
    baris.append("Deskripsi:")
    baris.append(hasil.deskripsi)
    baris.append(f"Tag: {', '.join(hasil.tags)}")
    if hasil.pelanggaran:
        baris.append(f"Peringatan: {', '.join(hasil.pelanggaran)}")
    return "\n".join(baris)


def main(argv: list[str] | None = None) -> int:
    argumen = _buat_parser().parse_args(argv)

    try:
        daftar_produk = _baca_produk(argumen.input)
        daftar_hasil = generate_batch(daftar_produk, argumen.platform, argumen.tone)

        if argumen.out:
            isi = ekspor_csv(daftar_hasil)
            with open(argumen.out, "w", encoding="utf-8", newline="") as berkas:
                berkas.write(isi)
            print(f"Tersimpan: {argumen.out} ({len(daftar_hasil)} produk)")
        else:
            print("\n\n".join(_format_hasil(hasil) for hasil in daftar_hasil))
    except (ValueError, FileNotFoundError) as galat:
        print(f"GALAT: {galat}", file=sys.stderr)
        return 1

    return 0
