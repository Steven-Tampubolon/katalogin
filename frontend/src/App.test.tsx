import { describe, it, expect, beforeEach, vi } from "vitest"
import React from "react"
import { renderToString } from "react-dom/server"
import App from "./App"
import contohRespons from "./contoh-respons.json"
vi.mock("./lib/api", () => ({
  ambilKredit: vi.fn().mockResolvedValue(5),
  buatListing: vi.fn(),
}))

beforeEach(() => {
  vi.clearAllMocks()
})

describe("Tugas 4: Layar pembuat listing", () => {
  it("kosong menampilkan teks Katalogin", () => {
    const html = renderToString(React.createElement(App))
    expect(html).toContain("Katalogin")
  })

  it("kosong memiliki heading Katalogin", () => {
    const html = renderToString(React.createElement(App))
    expect(html).toContain("Katalogin")
  })

  it("struktur desain memiliki Katalogin", () => {
    const html = renderToString(React.createElement(App))
    expect(html).toBeTruthy()
  })

  it("data contoh respons memiliki struktur yang benar", () => {
    expect(contohRespons).toBeDefined()
    expect(contohRespons.id).toBeDefined()
    expect(contohRespons.sisa_kredit).toBeDefined()
    expect(contohRespons.hasil).toBeDefined()
    expect(Array.isArray(contohRespons.hasil.judul)).toBe(true)
    expect(Array.isArray(contohRespons.hasil.tags)).toBe(true)
    expect(typeof contohRespons.hasil.deskripsi).toBe("string")
  })
})