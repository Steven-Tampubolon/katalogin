import { buatListing } from "./lib/api"
import * as React from "react"

const platforms = ["Shopee", "Tokopedia", "TikTok Shop"]
const tones = ["Kasual", "Profesional", "Singkat"]

type Hasil = {
  id: number
  hasil: any
  sisa_kredit: number
  ekstraksi?: string | undefined
  alasan_fallback?: string | undefined
  catatan_ai?: string | undefined
}

function App() {
  const [sisaKredit, setSisaKredit] = React.useState(0)
  const [infoProduk, setInfoProduk] = React.useState("")
  const [platform, setPlatform] = React.useState<"shopee" | "tokopedia" | "tiktok">("shopee")
  const [tone, setTone] = React.useState<"kasual" | "profesional" | "singkat">("kasual")
  const [gunaAi, setGunaAi] = React.useState(false)
  const [status, setStatus] = React.useState<"kosong" | "memuat" | "galat" | "sukses">("kosong")
  const [hasil, setHasil] = React.useState<Hasil | null>(null)
  const [proses, setProses] = React.useState(false)

  React.useEffect(() => {
    // ambilKredit tidak digunakan dalam implementasi sederhana
  }, [])

  const handleGenerate = async () => {
    if (!infoProduk.trim()) {
      setStatus("kosong")
      return
    }
    setStatus("memuat")
    setProses(true)
    setHasil(null)
    try {
      const data = await buatListing({ platform, tone, teks: infoProduk, gunakanAi: gunaAi })
      setHasil(data)
      setSisaKredit(data.sisa_kredit)
      setStatus("sukses")
    } catch {
      setStatus("galat")
    } finally {
      setProses(false)
    }
  }

  const handleCopy = (teks: string, btn: HTMLButtonElement) => {
    navigator.clipboard.writeText(teks)
    btn.textContent = "Tersalin"
    setTimeout(() => {
      btn.textContent = "Salin"
    }, 2000)
  }

  if (status === "kosong") {
    return (
      <div className="p-6 max-w-md mx-auto">
        <h2 className="text-2xl font-bold text-teks mb-2">Katalogin</h2>
        <p className="text-teks-redup mb-4">
          {infoProduk || "Tempel info produkmu di sini, nanti kami rapikan jadi judul, deskripsi, dan tag."}
        </p>
        <div className="mt-6 p-6 border rounded">
          <h3 className="font-semibold text-teks mb-4">Buat judul & deskripsi</h3>
          <textarea
            placeholder="Info produkmu..."
            value={infoProduk}
            onChange={(e) => setInfoProduk(e.target.value)}
            className="w-full rounded-md border py-3 text-teks focus:border-teks focus:ring-2 focus:ring-teks/50"
          />
          <div className="mt-4 grid grid-cols-1 gap-2">
            <label className="flex items-center gap-2">
              <span className="text-teks-redup">Platform</span>
              <select
                value={platform}
                onChange={(e) => setPlatform(e.target.value as any)}
                className="rounded-md border py-2 w-full"
              >
                {platforms.map((p) => (
                  <option key={p} value={p.toLowerCase()}>
                    {p}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2">
              <span className="text-teks-redup">Nada</span>
              <select
                value={tone}
                onChange={(e) => setTone(e.target.value as any)}
                className="rounded-md border py-2 w-full"
              >
                {tones.map((t) => (
                  <option key={t} value={t.toLowerCase()}>
                    {t}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="mt-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={gunaAi}
                onChange={(e) => setGunaAi(e.target.checked)}
                className="rounded-md border py-2"
              />
              <span className="text-teks-redup">Pakai AI untuk membaca info produk</span>
            </label>
          </div>
          <div className="mt-6">
            <button
              disabled={proses || status !== "kosong"}
              onClick={handleGenerate}
              className="w-full rounded-md border py-3 text-teks font-medium"
            >
              {proses ? "Menyusun…" : "Buat judul & deskripsi"}
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (status === "memuat") {
    return (
      <div className="p-6 max-w-md mx-auto">
        <h2 className="text-2xl font-bold text-teks mb-2">Katalogin</h2>
        <div className="mt-6 p-6 border rounded">
          <textarea
            placeholder="Info produk"
            disabled
            className="w-full rounded-md border py-3 text-teks"
            value=""
          />
          <div className="mt-4 grid grid-cols-1 gap-2">
            <label className="flex items-center gap-2">
              <span className="text-teks-redup">Platform</span>
              <select disabled className="rounded-md border py-2 w-full">
                <option value="shopee">Shopee</option>
                <option value="tokopedia">Tokopedia</option>
                <option value="tiktok">TikTok Shop</option>
              </select>
            </label>
            <label className="flex items-center gap-2">
              <span className="text-teks-redup">Nada</span>
              <select disabled className="rounded-md border py-2 w-full">
                <option value="kasual">Kasual</option>
                <option value="profesional">Profesional</option>
                <option value="singkat">Singkat</option>
              </select>
            </label>
          </div>
          <div className="mt-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                disabled
                checked={false}
                className="rounded-md border py-2"
              />
              <span className="text-sm text-teks-redup">Pakai AI untuk membaca info produk</span>
            </label>
          </div>
          <button disabled className="w-full rounded-md border py-3 text-teks font-medium">
            Buat judul & deskripsi
          </button>
        </div>
      </div>
    )
  }

  if (status === "galat") {
    return (
      <div className="p-6 max-w-md mx-auto">
        <h2 className="text-2xl font-bold text-teks mb-2">Katalogin</h2>
        <p className="text-teks">Belum berhasil. Coba lagi sebentar lagi.</p>
        <button className="w-full rounded-md border py-3 text-teks" onClick={() => setStatus("kosong")}>Coba lagi</button>
      </div>
    )
  }

  if (status === "sukses" && hasil) {
    return (
      <div className="p-6 max-w-2xl mx-auto">
        <h2 className="text-2xl font-bold text-teks mb-2">Katalogin</h2>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div>
            <h3 className="font-semibold text-teks mb-3">Hasil</h3>
            <div className="space-y-3">
              {hasil.hasil?.judul?.map((j: string, i: number) => (
                <div key={i} className="space-y-2">
                  <span className="text-teks line-clamp-3">{j}</span>
                </div>
              ))}
              <span className="text-teks line-clamp-3">{hasil.hasil?.deskripsi}</span>
              <div className="flex gap-2">
                {hasil.hasil?.tags?.map((t: string) => (
                  <span key={t} className="inline-flex items-center rounded-md bg-muted px-2.5 py-0.5 text-xs font-medium">
                    {t}
                  </span>
                ))}
                <button onClick={(e) => handleCopy(hasil.hasil?.tags?.join(", ") || "", e.currentTarget as HTMLButtonElement)} className="px-2.5 py-0.5 text-xs font-medium">
                  Salin semua tag
                </button>
              </div>
            </div>
          </div>
          <div>
            <span className="text-teks font-medium block mb-2">Sisa kredit: {sisaKredit}</span>
            <span>Tag: {hasil.hasil?.tags?.join(", ") || ""}</span>
          </div>
        </div>
      </div>
    )
  }

  return null
}

export default App