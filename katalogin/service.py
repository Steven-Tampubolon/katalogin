from dataclasses import dataclass

from katalogin import credits, db, history
from katalogin.models import Product
from katalogin.pipeline import Hasil, generate_batch


@dataclass
class HasilProses:
    ids: list[int]
    hasil: list[Hasil]
    sisa_kredit: int


def proses(
    db_path: str,
    user_id: str,
    daftar_produk: list[Product],
    platform: str,
    tone: str = "kasual",
    waktu: str | None = None,
) -> HasilProses:
    if not daftar_produk:
        raise ValueError("Daftar produk kosong")

    hasil = generate_batch(daftar_produk, platform, tone)
    waktu_terpakai = waktu if waktu else db.sekarang()
    koneksi = db.buka(db_path)
    try:
        with db.transaksi(koneksi):
            credits.pastikan_pengguna(koneksi, user_id, waktu_terpakai)
            sisa_kredit = credits.kurangi(
                koneksi, user_id, len(hasil), "generate", waktu_terpakai
            )
            ids = [
                history.simpan(koneksi, user_id, item, waktu_terpakai)
                for item in hasil
            ]
    finally:
        koneksi.close()

    return HasilProses(ids=ids, hasil=hasil, sisa_kredit=sisa_kredit)
