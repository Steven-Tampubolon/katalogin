import { useEffect, useState } from "react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import { ApiError, ambilKredit, buatListing } from "@/lib/api"

type Platform = "shopee" | "tokopedia" | "tiktok"
type Nada = "kasual" | "profesional" | "singkat"
type Status = "kosong" | "memuat" | "galat" | "sukses"
type Listing = {
  judul: string[]
  deskripsi: string
  tags: string[]
  peringatan?: string[]
}

const DAFTAR_PLATFORM: { nilai: Platform; label: string }[] = [
  { nilai: "shopee", label: "Shopee" },
  { nilai: "tokopedia", label: "Tokopedia" },
  { nilai: "tiktok", label: "TikTok Shop" },
]

const DAFTAR_NADA: { nilai: Nada; label: string }[] = [
  { nilai: "kasual", label: "Kasual" },
  { nilai: "profesional", label: "Profesional" },
  { nilai: "singkat", label: "Singkat" },
]

const PESAN_UMUM = "Belum berhasil. Coba lagi sebentar lagi."

function TombolSalin({ teks, nama }: { teks: string; nama: string }) {
  const [tersalin, setTersalin] = useState(false)

  async function salin() {
    try {
      await navigator.clipboard.writeText(teks)
    } catch {
      // Salinan gagal: tombol tetap menampilkan "Salin".
      return
    }
    setTersalin(true)
    setTimeout(() => setTersalin(false), 2000)
  }

  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      aria-label={`Salin ${nama}`}
      onClick={salin}
    >
      {tersalin ? "Tersalin" : "Salin"}
    </Button>
  )
}

function App() {
  const [kredit, setKredit] = useState<number | null>(null)
  const [teks, setTeks] = useState("")
  const [platform, setPlatform] = useState<Platform>("shopee")
  const [nada, setNada] = useState<Nada>("kasual")
  const [gunakanAi, setGunakanAi] = useState(false)
  const [status, setStatus] = useState<Status>("kosong")
  const [isianKosong, setIsianKosong] = useState(false)
  const [pesanGalat, setPesanGalat] = useState("")
  const [listing, setListing] = useState<Listing | null>(null)
  const [catatanAi, setCatatanAi] = useState("")

  useEffect(() => {
    ambilKredit()
      .then(setKredit)
      .catch(() => setKredit(null))
  }, [])

  async function buat() {
    if (teks.trim() === "") {
      setIsianKosong(true)
      return
    }
    setIsianKosong(false)
    setStatus("memuat")
    setPesanGalat("")
    setCatatanAi("")
    try {
      const data = await buatListing({ platform, tone: nada, teks, gunakanAi })
      setListing(data.hasil as Listing)
      setCatatanAi(data.catatan_ai ?? "")
      setKredit(data.sisa_kredit)
      setStatus("sukses")
    } catch (galat) {
      setPesanGalat(galat instanceof ApiError ? galat.pesan : PESAN_UMUM)
      setStatus("galat")
    }
  }

  const memuat = status === "memuat"

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="mx-auto flex w-full max-w-[640px] items-center justify-between px-4 py-6 lg:max-w-[1120px]">
        <h1 className="text-2xl font-bold">Katalogin</h1>
        <Badge variant="secondary" className="rounded-full">
          Kredit: {kredit ?? "…"}
        </Badge>
      </header>

      <main className="mx-auto grid w-full max-w-[640px] gap-6 px-4 pb-12 lg:max-w-[1120px] lg:grid-cols-2">
        <Card className="rounded-xl">
          <CardHeader>
            <h2 className="text-lg font-bold">Info produk</h2>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="info-produk">Info produk</Label>
              <Textarea
                id="info-produk"
                value={teks}
                onChange={(e) => setTeks(e.target.value)}
                placeholder="Contoh: Kaos polos pria, katun combed 30s, ukuran L, warna hitam"
                className="min-h-32"
              />
              {isianKosong && (
                <p className="text-sm text-destructive" role="alert">
                  Isi info produknya dulu ya.
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="platform">Platform</Label>
                <Select
                  value={platform}
                  onValueChange={(v) => setPlatform(v as Platform)}
                >
                  <SelectTrigger id="platform" className="h-11 w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {DAFTAR_PLATFORM.map((p) => (
                      <SelectItem key={p.nilai} value={p.nilai}>
                        {p.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="nada">Nada</Label>
                <Select value={nada} onValueChange={(v) => setNada(v as Nada)}>
                  <SelectTrigger id="nada" className="h-11 w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {DAFTAR_NADA.map((n) => (
                      <SelectItem key={n.nilai} value={n.nilai}>
                        {n.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Checkbox
                id="pakai-ai"
                checked={gunakanAi}
                onCheckedChange={(v) => setGunakanAi(v === true)}
              />
              <Label htmlFor="pakai-ai">Pakai AI untuk membaca info produk</Label>
            </div>

            <Button
              type="button"
              className="h-11 w-full"
              disabled={memuat}
              onClick={buat}
            >
              {memuat ? "Menyusun…" : "Buat judul & deskripsi"}
            </Button>
          </CardContent>
        </Card>

        <Card className="rounded-xl">
          <CardHeader>
            <h2 className="text-lg font-bold">Hasil</h2>
          </CardHeader>
          <CardContent className="space-y-4">
            {status === "kosong" && (
              <p className="text-muted-foreground">
                Tempel info produkmu di sini, nanti kami rapikan jadi judul,
                deskripsi, dan tag.
              </p>
            )}

            {status === "memuat" && (
              <div className="space-y-3" data-testid="skeleton-hasil">
                <Skeleton className="h-6 w-full" />
                <Skeleton className="h-6 w-5/6" />
                <Skeleton className="h-24 w-full" />
              </div>
            )}

            {status === "galat" && (
              <Alert variant="destructive">
                <AlertDescription>{pesanGalat}</AlertDescription>
              </Alert>
            )}

            {status === "sukses" && listing !== null && (
              <div className="space-y-5">
                {catatanAi !== "" && (
                  <Alert>
                    <AlertDescription>{catatanAi}</AlertDescription>
                  </Alert>
                )}

                {(listing.peringatan ?? []).length > 0 && (
                  <Alert>
                    <AlertDescription>
                      {(listing.peringatan ?? []).join(" ")}
                    </AlertDescription>
                  </Alert>
                )}

                <section className="space-y-3">
                  <h3 className="font-semibold">Judul</h3>
                  {listing.judul.map((judul, i) => (
                    <div
                      key={i}
                      className="flex items-start justify-between gap-3"
                    >
                      <p>{judul}</p>
                      <TombolSalin teks={judul} nama={`judul ${i + 1}`} />
                    </div>
                  ))}
                </section>

                <section className="space-y-3">
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="font-semibold">Deskripsi</h3>
                    <TombolSalin teks={listing.deskripsi} nama="deskripsi" />
                  </div>
                  <p className="whitespace-pre-line text-sm">
                    {listing.deskripsi}
                  </p>
                </section>

                <section className="space-y-3">
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="font-semibold">Tag</h3>
                    <TombolSalin
                      teks={listing.tags.join(", ")}
                      nama="semua tag"
                    />
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {listing.tags.map((tag) => (
                      <Badge
                        key={tag}
                        variant="secondary"
                        className="rounded-full"
                      >
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </section>
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  )
}

export default App
