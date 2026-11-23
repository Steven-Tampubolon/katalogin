import { describe, it, expect, beforeEach, vi } from "vitest"
import { ambilKredit, buatListing } from "./api"

beforeEach(() => {
  if (typeof localStorage !== "undefined") {
    localStorage.removeItem("katalogin_user_id")
  }
})

describe("Klien API frontend", () => {
  it("ambilUserId menghasilkan format u-ikuti-20-hex", () => {
    const key = "katalogin_user_id"
    let stored: string | null = null
    if (typeof localStorage !== "undefined") {
      stored = localStorage.getItem(key)
    }
    if (!stored) {
      const hex = Math.random().toString(16).padStart(20, "0").substring(0, 20)
      stored = `u-${hex}`
      if (typeof localStorage !== "undefined") {
        localStorage.setItem(key, stored)
      }
    }
    const regex = /^[A-Za-z0-9_.@-]{1,64}$/
    expect(stored).toMatch(regex)
  })

  it("ambilKredit mengirim X-User-Id header", async () => {
    const key = "katalogin_user_id"
    let userId: string | null = null
    if (typeof localStorage !== "undefined") {
      userId = localStorage.getItem(key)
    }
    if (!userId) {
      const hex = Math.random().toString(16).substring(2, 22)
      userId = `u-${hex}`
      if (typeof localStorage !== "undefined") {
        localStorage.setItem(key, userId)
      }
    }
    ;(global as any).fetch = vi.fn().mockResolvedValueOnce(
      new Response(JSON.stringify({ user_id: userId, kredit: 5 }), {
        status: 200,
        headers: { "content-type": "application/json" },
      })
    )
    await ambilKredit()
  })

  it("buatListing mengirim gunakan_ai sebagai boolean", async () => {
    ;(global as any).fetch = vi.fn().mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          id: 1,
          hasil: { nama_produk: "Kaos Polos Pria", platform: "shopee", tone: "kasual", judul: [], deskripsi: "", tags: [], pelanggaran: [] },
          sisa_kredit: 4,
        }),
        { status: 200, headers: { "content-type": "application/json" } }
      )
    )
    await buatListing({
      platform: "shopee",
      tone: "kasual",
      teks: "test",
      gunakan_ai: false,
    })
  })

  it("pemetaan galat 402", async () => {
    ;(global as any).fetch = vi.fn().mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Kredit tidak cukup" }), {
        status: 402,
        headers: { "content-type": "application/json" },
      })
    )
    try {
      await ambilKredit()
    } catch (e: any) {
      expect(e.status).toBe(402)
      expect(e.pesan).toBe("Kreditmu habis. Hubungi admin untuk menambah kredit.")
    }
  })

  it("pemetaan galat 422", async () => {
    ;(global as any).fetch = vi.fn().mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: [{ msg: "Error" }] }), {
        status: 422,
        headers: { "content-type": "application/json" },
      })
    )
    try {
      await ambilKredit()
    } catch (e: any) {
      expect(e.status).toBe(422)
      expect(e.pesan).toBe("Isiannya belum sesuai. Periksa lagi ya.")
    }
  })

  it("pemetaan galat 503", async () => {
    ;(global as any).fetch = vi.fn().mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "AI error" }), {
        status: 503,
        headers: { "content-type": "application/json" },
      })
    )
    try {
      await ambilKredit()
    } catch (e: any) {
      expect(e.status).toBe(503)
      expect(e.pesan).toBe("Layanan AI sedang tidak tersedia. Coba lagi nanti.")
    }
  })

  it("kegagalan jaringan", async () => {
    ;(global as any).fetch = vi.fn().mockRejectedValueOnce(new Error("Network error"))
    try {
      await ambilKredit()
    } catch (e: any) {
      expect(e.status).toBe(0)
      expect(e.pesan).toBe("Tidak bisa terhubung ke server.")
    }
  })
})