import sqlite3


KREDIT_GRATIS = 5


class KreditTidakCukup(Exception):
    def __init__(self, butuh: int, sisa: int) -> None:
        self.butuh = butuh
        self.sisa = sisa
        super().__init__(f"Kredit tidak cukup: butuh {butuh}, tersisa {sisa}")


def pastikan_pengguna(conn: sqlite3.Connection, user_id: str, waktu: str) -> bool:
    hasil = conn.execute(
        "INSERT OR IGNORE INTO pengguna(user_id, kredit, dibuat) VALUES (?, ?, ?)",
        (user_id, KREDIT_GRATIS, waktu),
    )
    if hasil.rowcount == 0:
        return False

    conn.execute(
        "INSERT INTO ledger(user_id, delta, alasan, dibuat) VALUES (?, ?, ?, ?)",
        (user_id, KREDIT_GRATIS, "gratis_awal", waktu),
    )
    return True


def saldo(conn: sqlite3.Connection, user_id: str) -> int:
    baris = conn.execute(
        "SELECT kredit FROM pengguna WHERE user_id = ?", (user_id,)
    ).fetchone()
    return 0 if baris is None else int(baris[0])


def kurangi(
    conn: sqlite3.Connection,
    user_id: str,
    jumlah: int,
    alasan: str,
    waktu: str,
) -> int:
    if jumlah <= 0:
        raise ValueError("Jumlah harus lebih dari 0")

    hasil = conn.execute(
        "UPDATE pengguna SET kredit = kredit - ? WHERE user_id = ? AND kredit >= ?",
        (jumlah, user_id, jumlah),
    )
    if hasil.rowcount == 0:
        raise KreditTidakCukup(butuh=jumlah, sisa=saldo(conn, user_id))

    conn.execute(
        "INSERT INTO ledger(user_id, delta, alasan, dibuat) VALUES (?, ?, ?, ?)",
        (user_id, -jumlah, alasan, waktu),
    )
    return saldo(conn, user_id)


def tambah(
    conn: sqlite3.Connection,
    user_id: str,
    jumlah: int,
    alasan: str,
    waktu: str,
) -> int:
    if jumlah <= 0:
        raise ValueError("Jumlah harus lebih dari 0")

    hasil = conn.execute(
        "UPDATE pengguna SET kredit = kredit + ? WHERE user_id = ?",
        (jumlah, user_id),
    )
    if hasil.rowcount == 0:
        raise ValueError("Pengguna tidak ditemukan")

    conn.execute(
        "INSERT INTO ledger(user_id, delta, alasan, dibuat) VALUES (?, ?, ?, ?)",
        (user_id, jumlah, alasan, waktu),
    )
    return saldo(conn, user_id)
