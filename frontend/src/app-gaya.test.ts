// @vitest-environment node
import { describe, it, expect } from "vitest"
import fs from "fs"
import path from "path"

const appPath = path.resolve("./src/App.tsx")
const cssPath = path.resolve("./src/index.css")

describe("Tugas 3: Verifikasi gaya dan impor", () => {
  it("App.tsx mengimpor dari komponen ui yang diperlukan", () => {
    const content = fs.readFileSync(appPath, "utf-8")
    expect(content).toContain("@/components/ui/button")
    expect(content).toContain("@/components/ui/card")
    expect(content).toContain("@/components/ui/textarea")
    expect(content).toContain("@/components/ui/select")
    expect(content).toContain("@/components/ui/label")
    expect(content).toContain("@/components/ui/badge")
    expect(content).toContain("@/components/ui/alert")
    expect(content).toContain("@/components/ui/skeleton")
  })

  it("App.tsx tidak menggunakan tag HTML mentah langsung", () => {
    const content = fs.readFileSync(appPath, "utf-8")
    // Cek kas sensitif - source menggunakan <Button>, <Select> dll (capital)
    expect(content).not.toContain('<button ')
    expect(content).not.toContain('<select ')
    expect(content).not.toContain('<textarea ')
    expect(content).not.toContain('<input ')
    expect(content).not.toContain('<label ')
  })

  it("Source CSS mengandung token warna dasar", () => {
    const content = fs.readFileSync(cssPath, "utf-8")
    expect(content).toContain("--primary")
    expect(content).toContain("--background")
    expect(content).toContain("--radius")
  })
})