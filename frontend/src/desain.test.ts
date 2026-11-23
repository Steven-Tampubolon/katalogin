import { describe, it, expect } from "vitest"
import React from "react"
import { renderToString } from "react-dom/server"
import fs from "fs"
import path from "path"
import App from "./App"

const lightHexes = {
  latar: "#FFFFFF",
  permukaan: "#F6F6F7",
  garis: "#E4E4E7",
  "garis-kontrol": "#78716C",
  teks: "#1C1917",
  "teks-redup": "#57534E",
  aksen: "#C2410C",
  "aksen-teks": "#FFFFFF",
  "aksen-lembut": "#FFEDD5",
  "aksen-lembut-teks": "#7C2D12",
  bahaya: "#B91C1C",
}

const darkHexes = {
  latar: "#171717",
  permukaan: "#1F1F1F",
  garis: "#2E2E2E",
  "garis-kontrol": "#78716C",
  teks: "#FAFAF9",
  "teks-redup": "#A8A29E",
  aksen: "#FB923C",
  "aksen-teks": "#1C1917",
  "aksen-lembut": "#431407",
  "aksen-lembut-teks": "#FED7AA",
  bahaya: "#F87171",
}

describe("Desain frontend", () => {
  it("App merender teks 'Katalogin'", () => {
    const html = renderToString(React.createElement(App))
    expect(html).toContain("Katalogin")
  })

  it("src/index.css memuat setiap hex dari tabel token terang", () => {
    const cssContent = fs.readFileSync(path.resolve("./src/index.css"), "utf-8")
    for (const hex of Object.values(lightHexes)) {
      expect(cssContent).toContain(hex)
    }
  })

  it("src/index.css memuat setiap hex dari tabel token gelap dan @media prefers-color-scheme dark", () => {
    const cssContent = fs.readFileSync(path.resolve("./src/index.css"), "utf-8")
    for (const hex of Object.values(darkHexes)) {
      expect(cssContent).toContain(hex)
    }
    expect(cssContent).toContain("prefers-color-scheme: dark")
  })

it("Tidak ada nilai hex di src/ kecuali di tes desain.test.ts", () => {
    const srcDir = path.resolve("./src")
    const fs = require("fs")
    const files = fs.readdirSync(srcDir)
    for (const file of files) {
      const filePath = path.join(srcDir, file)
      const stat = fs.statSync(filePath)
      if (stat.isDirectory()) continue
      // Only check .ts and .tsx files, excluding the test file itself
      if (!file.endsWith(".ts") && !file.endsWith(".tsx")) continue
      if (file === "desain.test.ts") continue
      const content = fs.readFileSync(filePath, "utf-8")
      const hexMatches = content.match(/#[0-9a-fA-F]{3,8}/g)
      if (hexMatches) {
        throw new Error(`Found hex values in ${file}: ${hexMatches.join(", ")}`)
      }
    }
  })
})