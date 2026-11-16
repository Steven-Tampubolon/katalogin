# Katalogin

Katalogin menyediakan API FastAPI untuk mengubah data produk menjadi judul SEO, deskripsi, dan tag, dengan kredit per pengguna dan riwayat hasil.

## Menjalankan

Pasang dependensi lalu jalankan aplikasi dengan Uvicorn:

```bash
pip install -r requirements.txt
uvicorn katalogin.main:app
```

## Antarmuka web

Antarmuka Streamlit berjalan sebagai proses terpisah dari API. Pasang dependensi, lalu jalankan API di satu terminal:

```bash
uvicorn katalogin.main:app
```

Jalankan antarmuka di terminal lain:

```bash
streamlit run katalogin/web/app.py
```

Secara bawaan, antarmuka menghubungi API di `http://127.0.0.1:8000`. Gunakan variabel lingkungan `KATALOGIN_API_URL` pada proses Streamlit jika API berjalan di alamat lain:

```bash
export KATALOGIN_API_URL=http://127.0.0.1:8000
streamlit run katalogin/web/app.py
```

Antarmuka menyediakan empat tab:

- **Dari teks** mengubah teks mentah supplier menjadi judul, deskripsi, dan tag. Opsi **Pakai AI untuk membaca teks** memakai layanan AI di sisi API.
- **Dari foto** membaca produk dari gambar JPEG, PNG, atau WebP. Pembuatan dari foto memerlukan konfigurasi AI pada proses API.
- **Dari CSV** membuat listing untuk beberapa produk sekaligus dan menyediakan hasil CSV untuk diunduh.
- **Riwayat** menampilkan 20 riwayat terbaru beserta detail hasil yang dipilih.

Kolom `ID pengguna` di sidebar hanyalah placeholder untuk memilih data pengguna, bukan login dan tidak memberikan keamanan. Jangan membuka antarmuka ini ke internet publik tanpa mekanisme autentikasi. Pastikan konfigurasi AI disetel pada proses API sebelum menggunakan pembuatan dari foto atau opsi AI untuk membaca teks.

## Variabel lingkungan

| Variabel | Keterangan | Bawaan |
|---|---|---|
| `KATALOGIN_DB` | Lokasi berkas database SQLite | `katalogin.db` |
| `KATALOGIN_ADMIN_TOKEN` | Token untuk endpoint penambahan kredit admin | Tidak ada; endpoint admin menolak semua permintaan bila kosong |

Header `X-User-Id` pada endpoint pengguna hanyalah placeholder, bukan mekanisme autentikasi atau keamanan.

## Konfigurasi AI

| Variabel | Keterangan | Bawaan |
|---|---|---|
| `KATALOGIN_LLM_PROVIDER` | Penyedia LLM: `gemini` atau `openai` untuk API kompatibel OpenAI | `gemini` |
| `KATALOGIN_LLM_API_KEY` | Kunci API untuk provider `openai`; menjadi kunci cadangan untuk provider `gemini` bila `GEMINI_API_KEY` kosong | Tidak ada |
| `KATALOGIN_LLM_BASE_URL` | Alamat dasar API untuk provider `openai` | `https://api.openai.com/v1` |
| `KATALOGIN_LLM_MODEL` | Nama model yang digunakan; wajib diisi untuk provider `openai` | `gemini-3.6-flash` untuk provider `gemini` |
| `GEMINI_API_KEY` | Kunci API Gemini | Tidak ada; layanan AI dinonaktifkan bila kunci tidak tersedia |

Simpan kunci API sebagai variabel lingkungan di tempat API dijalankan. Jangan menyimpan kunci API di repository atau mencetaknya di log.

Contoh konfigurasi Gemini:

```bash
export KATALOGIN_LLM_PROVIDER=gemini
export GEMINI_API_KEY=<kunci>
export KATALOGIN_LLM_MODEL=gemini-3.6-flash
```

Contoh konfigurasi NVIDIA melalui API kompatibel OpenAI:

```bash
export KATALOGIN_LLM_PROVIDER=openai
export KATALOGIN_LLM_API_KEY=<kunci>
export KATALOGIN_LLM_BASE_URL=https://integrate.api.nvidia.com/v1
export KATALOGIN_LLM_MODEL=<model>
```

Contoh konfigurasi OpenRouter melalui API kompatibel OpenAI:

```bash
export KATALOGIN_LLM_PROVIDER=openai
export KATALOGIN_LLM_API_KEY=<kunci>
export KATALOGIN_LLM_BASE_URL=https://openrouter.ai/api/v1
export KATALOGIN_LLM_MODEL=<model>
```

Kode tidak memuat berkas `.env` secara otomatis. Ekspor variabel tersebut di shell atau gunakan pemuat `.env` pilihan Anda. Endpoint `/generate/foto` hanya berfungsi bila model yang dipilih mendukung gambar.

Opsi `gunakan_ai` pada `POST /generate` meminta penyedia AI mengekstraksi atribut produk dari `teks` supplier. Opsi ini hanya berlaku bila `teks` diisi dan tidak dapat dikombinasikan dengan `produk`. Contoh:

```json
{
  "platform": "shopee",
  "teks": "Kaos polos pria Oneck, katun combed 30s, warna hitam",
  "gunakan_ai": true
}
```

Satu produk hasil ekstraksi AI memakai 1 kredit, sama seperti pemrosesan produk biasa. Jika hasil AI tidak dapat dibaca, API memakai ekstraksi berbasis aturan.

`POST /generate/foto` menerima gambar produk dalam body JSON:

```json
{
  "platform": "shopee",
  "tone": "kasual",
  "gambar_base64": "<data base64>"
}
```

Gambar harus berformat JPEG, PNG, atau WebP dan ukurannya maksimal 5 MB. Setiap foto yang berhasil diproses memakai 1 kredit.

Galat API AI yang perlu diperhatikan:

- `502`: permintaan ke penyedia AI gagal saat memproses foto.
- `503`: layanan AI belum dikonfigurasi atau klien tidak mendukung pembacaan gambar.

Untuk menguji koneksi secara manual, jalankan:

```bash
python -m katalogin.uji_llm
python -m katalogin.uji_llm --foto <berkas>
```

Perintah pertama menguji balasan teks, sedangkan perintah kedua menguji pembacaan foto.

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
| `POST` | `/generate/foto` | Mengekstraksi produk dari foto dan menghasilkan konten |
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
