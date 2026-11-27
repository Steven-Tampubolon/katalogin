// @vitest-environment node
import { existsSync, readdirSync, readFileSync } from "node:fs"
import { join } from "node:path"
import { describe, expect, it } from "vitest"

const UI = "src/components/ui"
const EKSPOR: Record<string, string[]> = {
  "button.tsx": ["Button", "buttonVariants"],
  "card.tsx": ["Card", "CardHeader", "CardContent"],
  "select.tsx": ["Select", "SelectTrigger", "SelectValue", "SelectContent", "SelectItem"],
  "badge.tsx": ["Badge", "badgeVariants"],
  "alert.tsx": ["Alert", "AlertDescription"],
  "skeleton.tsx": ["Skeleton"],
  "textarea.tsx": ["Textarea"],
  "label.tsx": ["Label"],
  "checkbox.tsx": ["Checkbox"],
}

describe("komponen shadcn", () => {
  it("tidak ada folder literal @ hasil CLI yang salah alamat", () => {
    expect(existsSync("@")).toBe(false)
  })

  it("sembilan komponen ada di src/components/ui dan mengekspor nama yang dipakai", () => {
    for (const [berkas, nama] of Object.entries(EKSPOR)) {
      const jalur = join(UI, berkas)
      expect(existsSync(jalur), jalur).toBe(true)
      const isi = readFileSync(jalur, "utf8")
      expect(isi, jalur).toContain("export")
      for (const n of nama) {
        expect(new RegExp(`\\b${n}\\b`).test(isi), `${jalur}: ${n}`).toBe(true)
      }
    }
  })

  it("utils.ts memakai clsx dan tailwind-merge, bukan cn buatan sendiri", () => {
    const isi = readFileSync("src/lib/utils.ts", "utf8")
    expect(isi).toContain("twMerge")
    expect(isi).toContain("clsx")
  })

  it("tidak ada komponen yang mengimpor paket bernama cn, dan paket cn tidak terpasang", () => {
    for (const f of readdirSync(UI).filter((x) => x.endsWith(".tsx"))) {
      const isi = readFileSync(join(UI, f), "utf8")
      expect(/from\s+["']cn["']/.test(isi), f).toBe(false)
    }
    const pkg = JSON.parse(readFileSync("package.json", "utf8"))
    expect(Object.keys({ ...pkg.dependencies, ...pkg.devDependencies })).not.toContain("cn")
  })

  it("setiap paket pihak ketiga yang diimpor komponen ada di package.json", () => {
    const pkg = JSON.parse(readFileSync("package.json", "utf8"))
    const ada = new Set([
      ...Object.keys(pkg.dependencies ?? {}),
      ...Object.keys(pkg.devDependencies ?? {}),
    ])
    const kurang = new Set<string>()
    for (const f of readdirSync(UI).filter((x) => x.endsWith(".tsx"))) {
      const isi = readFileSync(join(UI, f), "utf8")
      for (const m of isi.matchAll(/(?:from|import)\s+["']([^"']+)["']/g)) {
        const s = m[1]
        if (s.startsWith(".") || s.startsWith("@/")) continue
        const nama = s.startsWith("@") ? s.split("/").slice(0, 2).join("/") : s.split("/")[0]
        if (nama !== "react" && nama !== "react-dom" && !ada.has(nama)) kurang.add(nama)
      }
    }
    expect([...kurang]).toEqual([])
  })
})
