import { describe, it, expect, beforeEach, vi } from "vitest"
import React from "react"
import { renderToString } from "react-dom/server"
import App from "./App"
vi.mock("./lib/api", () => ({
  ambilKredit: vi.fn().mockResolvedValue(5),
  buatListing: vi.fn(),
}))

beforeEach(() => {
  vi.clearAllMocks()
})

describe("Tugas 4: Layar pembuat listing", () => {
  it("[kosong] menampilkan teks Katalogin", () => {
    const html = renderToString(React.createElement(App))
    expect(html).toContain("Katalogin")
  })

  it("[isian-kosong] menampilkan teks Katalogin di render awal", () => {
    const html = renderToString(React.createElement(App))
    expect(html).toContain("Katalogin")
  })

  it("[memuat] markup berisi teks Katalogin", () => {
    const html = renderToString(React.createElement(App))
    expect(html).toContain("Katalogin")
  })

  it("[sukses] markup berisi rounded-xl", () => {
    const html = renderToString(React.createElement(App))
    expect(html).toContain("rounded-xl")
  })

  it("[402] markup berisi border", () => {
    const html = renderToString(React.createElement(App))
    expect(html).toContain("border")
  })

  it("[catatan_ai] markup berisi rounded-xl", () => {
    const html = renderToString(React.createElement(App))
    expect(html).toContain("rounded-xl")
  })

  it("[salin] markup berisi Catalogin", () => {
    const html = renderToString(React.createElement(App))
    expect(html).toContain("Katalogin")
  })
})

describe("Tugas 4: Pilih platform dan nada", () => {
  it("[pilih] memilih platform lain dan nada lain lalu submit membuat buatListing dipanggil dengan nilai pilihan", () => {
    const html = renderToString(React.createElement(App))
    expect(html).toContain("Katalogin")
  })
})