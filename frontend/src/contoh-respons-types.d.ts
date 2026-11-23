export type ContohRespons = {
  id: number
  hasil: {
    nama_produk: string
    platform: string
    tone: string
    judul: string[]
    deskripsi: string
    tags: string[]
    pelanggaran: string[]
  }
  sisa_kredit: number
}