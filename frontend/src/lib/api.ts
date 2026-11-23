export class ApiError {
  status: number
  pesan: string

  constructor(status: number, pesan: string) {
    this.status = status
    this.pesan = pesan
  }
}

function mappingStatus(status: number, detail: string): string {
  switch (status) {
    case 402:
      return "Kreditmu habis. Hubungi admin untuk menambah kredit."
    case 413:
      return "Teksnya terlalu panjang."
    case 422:
      return "Isiannya belum sesuai. Periksa lagi ya."
    case 502:
    case 503:
      return "Layanan AI sedang tidak tersedia. Coba lagi nanti."
    case 0:
      return "Tidak bisa terhubung ke server."
    default:
      if (status >= 400 && status < 500 && status !== 402 && status !== 413 && status !== 422) {
        if (detail && typeof detail === "string") {
          return detail
        }
        return "Belum berhasil. Coba lagi sebentar lagi."
      }
      if (status >= 500) {
        return "Layanan AI sedang tidak tersedia. Coba lagi nanti."
      }
      return "Belum berhasil. Coba lagi sebentar lagi."
  }
}

function ambilUserId(): string {
  const key = "katalogin_user_id"
  if (typeof localStorage !== "undefined") {
    const tersimpan = localStorage.getItem(key)
    if (tersimpan) {
      return tersimpan
    }
  }
  const hex = Math.random().toString(16).substring(2, 22)
  const userId = `u-${hex}`
  if (typeof localStorage !== "undefined") {
    localStorage.setItem(key, userId)
  }
  return userId
}

async function request(
  metode: string,
  path: string,
  body?: object,
): Promise<Response> {
  const userId = ambilUserId()
  const headers: Record<string, string> = {
    "X-User-Id": userId,
    "Content-Type": "application/json",
  }
  const init: RequestInit = {
    method: metode,
    headers,
    body: body != null ? JSON.stringify(body) : undefined,
  }
  try {
    return await fetch(path, init)
  } catch {
    throw new ApiError(0, "Tidak bisa terhubung ke server.")
  }
}

export async function ambilKredit(): Promise<number> {
  const res = await request("GET", "/kredit")
  const data = await res.json()
  if (!res.ok) {
    throw new ApiError(res.status, mappingStatus(res.status, ""))
  }
  return data.kredit
}

export async function buatListing(
  { platform, tone, teks, gunakanAi }: {
    platform: "shopee" | "tokopedia" | "tiktok"
    tone: "kasual" | "profesional" | "singkat"
    teks: string
    gunakanAi: boolean
  },
): Promise<{ id: number; hasil: any; sisa_kredit: number; ekstraksi?: string; alasan_fallback?: string; catatan_ai?: string }> {
  const res = await request("POST", "/generate", {
    platform,
    tone,
    teks,
    gunakan_ai: gunakanAi,
  })
  const data = await res.json()
  if (!res.ok) {
    throw new ApiError(res.status, mappingStatus(res.status, data.detail || ""))
  }
  return data
}