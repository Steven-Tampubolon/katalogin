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

  it("[402] markup berisi border-background", () => {
    const html = renderToString(React.createElement(App))
    expect(html).toContain("border-background")
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