// @vitest-environment node
// @ts-nocheck
import { describe, it, expect } from "vitest"
import { readFileSync } from "fs"
import path from "path"

describe("Tugas 1: Tailwind v4, alias, dan token", () => {
  const pkg = JSON.parse(readFileSync(path.resolve("./package.json"), "utf-8"))
  const css = readFileSync(path.resolve("./src/index.css"), "utf-8")
  const cssLines = css.split("\n")
  const viteConfig = readFileSync(path.resolve("./vite.config.ts"), "utf-8")

  it("package.json tidak memuat @shadcn/ui dan vite-tsconfig-paths", () => {
    expect(pkg.dependencies["@shadcn/ui"]).toBeUndefined()
    expect(pkg.dependencies["vite-tsconfig-paths"]).toBeUndefined()
    expect(pkg.devDependencies["@shadcn/ui"]).toBeUndefined()
    expect(pkg.devDependencies["vite-tsconfig-paths"]).toBeUndefined()
  })

  it(" versi @tailwindcss/vite sama dengan tailwindcss dan tanpa ^ atau ~", () => {
    const tcwVersion = pkg.devDependencies["@tailwindcss/vite"]
    const twVersion = pkg.devDependencies["tailwindcss"]
    expect(tcwVersion).toBe(twVersion)
    expect(tcwVersion).not.toMatch(/^[\^~]/)
  })

  it("vite.config.ts memuat @tailwindcss/vite dan tailwindcss()", () => {
    expect(viteConfig).toContain("@tailwindcss/vite")
    expect(viteConfig).toContain("tailwindcss()")
  })

  it("baris pertama index.css persis @import \"tailwindcss\"; dan memuat @theme inline, --color-primary-hover, --color-success, tidak memuat @tailwind ", () => {
    expect(cssLines[0]).toBe(`@import "tailwindcss";`)
    expect(css).toContain("@theme inline")
    expect(css).toContain("--color-primary-hover")
    expect(css).toContain("--color-success")
    expect(css).not.toContain("@tailwind ")
  })
})