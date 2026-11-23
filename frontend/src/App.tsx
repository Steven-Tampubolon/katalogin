import { buatListing } from "./lib/api"
import * as React from "react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectTrigger, SelectContent, SelectValue, SelectSeparator } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"

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
      const data = await buatListing({ platform: "shopee" as any, tone: "kasual" as any, teks: infoProduk, gunakanAi: false })
      setHasil(data)
      setSisaKredit(data.sisa_kredit)
      setStatus("sukses")
    } catch (e) {
      const err = e as { status?: number; pesan?: string }
      if (err.status === 402) {
        setStatus("galat")
      } else {
        setStatus("galat")
      }
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

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="max-w-640 mx-auto py-6">
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader className="pb-3 border-b border-background">
              <h2 className="text-2xl font-bold text-teks">Katalogin</h2>
              <div className="mt-2 flex items-center gap-2">
                <span className="text-teks-redup">Sisa kredit: 5</span>
                <Badge>5</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <Textarea
                placeholder="Info produk"
                value={infoProduk}
                onChange={(e) => setInfoProduk(e.target.value)}
                disabled={proses}
              />
              <div className="mt-4 grid grid-cols-1 gap-2">
                <Label>
                  <span className="text-teks-redup">Platform</span>
                  <Select>
                    <SelectTrigger>
                      <span className="text-sm font-medium">Shopee</span>
                    </SelectTrigger>
                    <SelectContent>
                      {platforms.map((p) => (
                        <React.Fragment key={p}>
                          <SelectSeparator />
                          <SelectValue>{p}</SelectValue>
                        </React.Fragment>
                      ))}
                    </SelectContent>
                  </Select>
                </Label>
                <Label className="mt-4">
                  <span className="text-teks-redup">Nada</span>
                  <Select>
                    <SelectTrigger>
                      <span className="text-sm font-medium">Kasual</span>
                    </SelectTrigger>
                    <SelectContent>
                      {tones.map((t) => (
                        <React.Fragment key={t}>
                          <SelectSeparator />
                          <SelectValue>{t}</SelectValue>
                        </React.Fragment>
                      ))}
                    </SelectContent>
                  </Select>
                </Label>
              </div>
              <div className="mt-4">
                <Label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    defaultChecked
                    className="rounded-md border py-2"
                  />
                  <span className="text-teks-redup">Pakai AI untuk membaca info produk</span>
                </Label>
              </div>
              <div className="mt-6">
                <Button
                  disabled={proses || status !== "kosong"}
                  onClick={handleGenerate}
                >
                  {proses ? "Menyuling…" : "Buat judul & deskripsi"}
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3 border-b border-background">
              <h2 className="text-2xl font-bold text-teks">Hasil</h2>
            </CardHeader>
            <CardContent>
              {status === "kosong" && (
                <p className="text-teks-redup">
                  Isi info produknya dulu ya.
                </p>
              )}

              {status === "memuat" && (
                <div className="mt-4">
                  <Skeleton className="h-6 w-full rounded-md mb-2" />
                  <Skeleton className="h-6 w-2/3 rounded-md mb-2" />
                  <Skeleton className="h-6 w-3/4 rounded-md mb-2" />
                </div>
              )}

              {status === "galat" && (
                <Alert>
                  <AlertDescription>{"Belum berhasil. Coba lagi sebentar lagi."}</AlertDescription>
                </Alert>
              )}

              {status === "sukses" && hasil && (
                <div className="space-y-4">
                  {["judul", "judul2", "judul3"].map((key, i) => {
                    const judul = (hasil.hasil as any)[key] as string | undefined
                    return (
                      <div key={i} className="space-y-2">
                        <span className="text-teks line-clamp-3">{judul}</span>
                        <Badge onClick={(e) => handleCopy(judul || "", e.currentTarget as HTMLButtonElement)}>Salin</Badge>
                      </div>
                    )
                  })}

                  <span className="text-teks font-medium block mb-2">Sisa kredit: {sisaKredit}</span>

                  <span>Tag: {(hasil.hasil as any).tags?.join(", ") || ""}</span>

                  <span className="text-teks line-clamp-3">
                    {(hasil.hasil as any).deskripsi}
                  </span>

                  {(hasil.catatan_ai as string | undefined) && (
                    <Alert>
                      <AlertDescription>{hasil.catatan_ai}</AlertDescription>
                    </Alert>
                  )}

                  <div className="flex gap-2">
                    <Badge onClick={(e) => handleCopy((hasil.hasil as any).deskripsi || "", e.currentTarget as HTMLButtonElement)}>Salin</Badge>
                    <Badge onClick={(e) => handleCopy((hasil.hasil as any).tags?.join(", ") || "", e.currentTarget as HTMLButtonElement)} className="px-2.5 py-0.5 text-xs font-medium">
                      Salin semua tag
                    </Badge>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default App