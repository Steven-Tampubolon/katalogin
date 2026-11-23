# DESIGN.md — Katalogin

Sumber kebenaran gaya untuk semua pekerjaan antarmuka Katalogin (manusia maupun VELOX). Bila ada konflik dengan skill desain, berkas ini menang.

## Produk dan pengguna
Katalogin membantu penjual UMKM di Shopee, Tokopedia, dan TikTok Shop mengubah info produk mentah (teks; nanti foto dan CSV) menjadi tiga variasi judul, satu deskripsi, dan tag yang siap ditempel. Penggunanya penjual kecil yang sering memakai HP, tidak teknis, dan punya waktu sedikit. Tugas utamanya: tempel info produk, pilih platform dan nada, lalu salin hasilnya.

## Kesan
Ramah, ceria, jelas. Keceriaan datang dari bentuk (sudut membulat), bobot huruf, warna aksen oranye, dan nada tulisan; bukan dari dekorasi.

## Warna
Mode tampilan mengikuti pengaturan perangkat (`prefers-color-scheme`). Tidak ada tombol pengalih.

| Token | Terang | Gelap | Peran |
|---|---|---|---|
| `latar` | `#FFFFFF` | `#171717` | latar halaman |
| `permukaan` | `#F6F6F7` | `#1F1F1F` | kartu, panel |
| `garis` | `#E4E4E7` | `#2E2E2E` | pemisah dekoratif |
| `garis-kontrol` | `#78716C` | `#78716C` | batas kolom isian (kontras minimal 3:1) |
| `teks` | `#1C1917` | `#FAFAF9` | teks utama |
| `teks-redup` | `#57534E` | `#A8A29E` | teks pendukung |
| `aksen` | `#C2410C` | `#FB923C` | tombol utama, fokus, sorotan |
| `aksen-teks` | `#FFFFFF` | `#1C1917` | teks di atas `aksen` |
| `aksen-hover` | `#9A3412` | `#FDBA74` | tombol utama saat disorot |
| `aksen-lembut` | `#FFEDD5` | `#431407` | latar sorotan lembut |
| `aksen-lembut-teks` | `#7C2D12` | `#FED7AA` | teks di atas `aksen-lembut` |
| `sukses` | `#15803D` | `#4ADE80` | keadaan berhasil |
| `bahaya` | `#B91C1C` | `#F87171` | galat |

Rasio kontras teks (dihitung dengan rumus WCAG): `teks` pada `latar` 17,49 (terang) dan 17,17 (gelap); `teks-redup` pada `permukaan` 7,06 dan 6,54; `aksen-teks` pada `aksen` 5,18 dan 7,73; `aksen-lembut-teks` pada `aksen-lembut` 8,18 dan 11,56; `sukses` pada `permukaan` 4,64 dan 9,46; `bahaya` pada `permukaan` 5,99 dan 5,96. Semua di atas 4,5. Aksen oranye dipakai untuk aksi utama, cincin fokus, dan sorotan hasil, bukan untuk latar besar.

## Tipografi
- Satu keluarga: Plus Jakarta Sans (paket `@fontsource-variable/plus-jakarta-sans`, nama CSS `Plus Jakarta Sans Variable`), cadangan `system-ui, sans-serif`.
- Skala (px): 14, 16, 18, 24, 32. Isi 16 px bobot 400, tinggi baris 1,5. Judul bobot 700, tinggi baris 1,2. Tombol bobot 600.

## Jarak dan radius
- Jarak kelipatan 4 px: 4, 8, 12, 16, 24, 32, 48.
- Radius: kontrol 10 px, panel 16 px, tag berbentuk pil (9999 px).
- Tanpa bayangan besar. Panel dibedakan dari latar oleh garis 1 px berwarna `garis`. Cincin fokus: 2 px `aksen` dengan jarak 2 px.

## Komponen
shadcn/ui: Button, Card, Select, Textarea, Label, Badge, Alert, Skeleton, Checkbox. Ikon dari `lucide-react`. Target sentuh utama minimal 44 px.

## Tata letak
Mobile (di bawah 1024 px): satu kolom, lebar isi maksimum 640 px dan di tengah. Desktop (1024 px ke atas): dua kolom (formulir kiri, hasil kanan), lebar maksimum 1120 px.

```
+--------------------------------------------------+
| Katalogin                       [ Kredit: 5 ]    |
+----------------------+---------------------------+
| Info produk          | Hasil                     |
| [ textarea        ]  | Judul 1  [Salin]          |
| Platform [v] Nada[v] | Judul 2  [Salin]          |
| [ ] Pakai AI         | Judul 3  [Salin]          |
| [Buat judul & ...]   | Deskripsi [Salin]         |
|                      | Tag: (pil) (pil) (pil)    |
+----------------------+---------------------------+
```

## Gaya yang dihindari
Gradasi dekoratif; kartu identik berbaris dengan bayangan yang sama; ikon di dalam lingkaran berwarna di atas setiap judul; label HURUF BESAR kecil di atas setiap judul; emoji sebagai ikon fungsi; animasi masuk pada tiap bagian; satu radius yang sama untuk semua elemen.

## Bahasa dan nada teks
Bahasa Indonesia, menyapa dengan "kamu". Hangat tetapi jelas, kalimat pendek, tanpa emoji dekoratif. Contoh:
- Tombol utama: "Buat judul & deskripsi"; saat diproses: "Menyusun…".
- Keadaan kosong: "Tempel info produkmu di sini, nanti kami rapikan jadi judul, deskripsi, dan tag."
- Isian kosong: "Isi info produknya dulu ya."
- Kredit habis (402): "Kreditmu habis. Hubungi admin untuk menambah kredit."
- Galat umum: "Belum berhasil. Coba lagi sebentar lagi."
- Tombol salin: "Salin"; setelah diklik 2 detik: "Tersalin".

## Keadaan wajib
Setiap layar yang memuat data punya: kosong, memuat, galat, sukses. Tombol aksi menampilkan keadaan sedang memproses dan tidak dapat diklik dua kali.
