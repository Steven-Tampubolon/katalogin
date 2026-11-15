import argparse
import sys
from collections.abc import Callable, Mapping
from pathlib import Path

from katalogin.gambar import deteksi_mime
from katalogin.llm import LLMClient, LLMError
from katalogin.llm_config import buat_klien_dari_env


BuatKlien = Callable[[Mapping[str, str] | None], LLMClient | None]


def _buat_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m katalogin.uji_llm",
        description="Uji koneksi dan pembacaan gambar oleh Gemini.",
    )
    parser.add_argument(
        "--foto",
        metavar="JALUR",
        help="Jalur foto produk untuk diuji",
    )
    return parser


def _galat(pesan: str) -> int:
    print(f"GALAT: {pesan}", file=sys.stderr)
    return 1


def main(
    argv: list[str] | None = None,
    env: Mapping[str, str] | None = None,
    buat_klien: BuatKlien | None = None,
) -> int:
    argumen = _buat_parser().parse_args(argv)
    builder = buat_klien if buat_klien is not None else buat_klien_dari_env

    try:
        klien = builder(env)
    except LLMError as galat:
        return _galat(str(galat))

    if klien is None:
        return _galat("GEMINI_API_KEY belum diisi")

    try:
        if argumen.foto is None:
            balasan = klien.complete("Jawab satu kata: halo")
        else:
            try:
                gambar = Path(argumen.foto).read_bytes()
            except FileNotFoundError:
                return _galat(f"Berkas tidak ditemukan: {argumen.foto}")
            except OSError as galat:
                return _galat(str(galat))

            try:
                mime = deteksi_mime(gambar)
            except ValueError as galat:
                return _galat(str(galat))

            balasan = klien.complete_dengan_gambar(
                "Sebutkan benda utama pada gambar ini dalam satu kalimat.",
                gambar,
                mime,
            )
    except LLMError as galat:
        return _galat(str(galat))

    print(f"Balasan AI: {balasan.strip()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
