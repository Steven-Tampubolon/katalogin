# Katalogin

Katalogin menyediakan API FastAPI untuk mengubah data produk menjadi judul SEO, deskripsi, dan tag, dengan kredit per pengguna dan riwayat hasil.

## Menjalankan

Pasang dependensi lalu jalankan aplikasi dengan Uvicorn:

```bash
pip install -r requirements.txt
uvicorn katalogin.main:app
```

## Variabel lingkungan

| Variabel | Keterangan | Bawaan |
|---|---|---|
| `KATALOGIN_DB` | Lokasi berkas database SQLite | `katalogin.db` |
| `KATALOGIN_ADMIN_TOKEN` | Token untuk endpoint penambahan kredit admin | Tidak ada; endpoint admin menolak semua permintaan bila kosong |

Header `X-User-Id` pada endpoint pengguna hanyalah placeholder, bukan mekanisme autentikasi atau keamanan.

## Batas masukan

- `nama`, `merek`, `bahan`, `ukuran`, `warna`, dan `fungsi` produk: masing-masing maksimum 200 karakter.
- `fitur` produk: maksimum 20 item, masing-masing item maksimum 100 karakter.
- `teks` pada `POST /generate`: maksimum 20000 karakter.
- `platform` dan `tone` pada `POST /generate` serta `POST /generate/csv`: masing-masing maksimum 30 karakter.
- `csv` pada `POST /generate/csv`: maksimum 100000 karakter.
- `user_id` pada `POST /admin/kredit`: maksimum 64 karakter.
- Body permintaan dibatasi maksimal 1000000 byte. Permintaan yang melebihi batas ditolak dengan status 413 dan JSON `{"detail": "Permintaan terlalu besar"}`. Batas berlaku berdasarkan `Content-Length` maupun jumlah byte pada stream body, sehingga permintaan chunked atau tanpa `Content-Length` juga dibatasi.

## Endpoint

| Metode | Jalur | Keterangan |
|---|---|---|
| `GET` | `/health` | Memeriksa kesehatan aplikasi |
| `GET` | `/kredit` | Mengambil saldo kredit pengguna |
| `POST` | `/generate` | Menghasilkan konten dari satu produk |
| `POST` | `/generate/csv` | Menghasilkan konten dari beberapa produk dalam CSV |
| `GET` | `/riwayat` | Mengambil daftar riwayat hasil pengguna |
| `GET` | `/riwayat/{id}` | Mengambil satu riwayat hasil milik pengguna |
| `POST` | `/admin/kredit` | Menambah kredit pengguna dengan header `X-Admin-Token` |

## Contoh Permintaan

```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H 'Content-Type: application/json' \
  -H 'X-User-Id: andi' \
  -d '{"platform":"shopee","produk":{"nama":"Kaos Polos Pria","merek":"Oneck"}}'
```
