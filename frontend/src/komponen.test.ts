// @vitest-environment node
// @ts-nocheck
import { describe, it, expect } from "vitest"
import fs from "fs"
import path from "path"

const uiDir = path.resolve("./src/components/ui")
const files = fs.readdirSync(uiDir)

describe("Tugas 2: Komponen shadcn dan gaya", () => {
  it("sembilan berkas komponen ada di src/components/ui/", () => {
    const expected = [
      "button.tsx",
      "card.tsx",
      "select.tsx",
      "textarea.tsx",
      "label.tsx",
      "badge.tsx",
      "alert.tsx",
      "skeleton.tsx",
      "checkbox.tsx",
    ]
    for (const f of expected) {
      expect(files).toContain(f)
    }
  })

  it("memuat ekspor buttonVarians dari button.tsx", () => {
    const button = fs.readFileSync(path.resolve("./src/components/ui/button.tsx"), "utf-8")
    expect(button).toContain("buttonVariants")
  })

  it("memuat ekspor CardContent dari card.tsx", () => {
    const card = fs.readFileSync(path.resolve("./src/components/ui/card.tsx"), "utf-8")
    expect(card).toContain("CardContent")
  })

  it("memuat ekspor SelectTrigger dari select.tsx", () => {
    const select = fs.readFileSync(path.resolve("./src/components/ui/select.tsx"), "utf-8")
    expect(select).toContain("SelectTrigger")
  })

  it("memuat ekspor SelectContent dari select.tsx", () => {
    const select = fs.readFileSync(path.resolve("./src/components/ui/select.tsx"), "utf-8")
    expect(select).toContain("SelectContent")
  })

  it("memuat ekspor badgeVariants dari badge.tsx", () => {
    const badge = fs.readFileSync(path.resolve("./src/components/ui/badge.tsx"), "utf-8")
    expect(badge).toContain("badgeVariants")
  })

  it("memuat ekspor AlertDescription dari alert.tsx", () => {
    const alert = fs.readFileSync(path.resolve("./src/components/ui/alert.tsx"), "utf-8")
    expect(alert).toContain("AlertDescription")
  })

  it("memuat ekspor Skeleton dari skeleton.tsx", () => {
    const skeleton = fs.readFileSync(path.resolve("./src/components/ui/skeleton.tsx"), "utf-8")
    expect(skeleton).toContain("Skeleton")
  })

  it("memuat ekspor Textarea dari textarea.tsx", () => {
    const textarea = fs.readFileSync(path.resolve("./src/components/ui/textarea.tsx"), "utf-8")
    expect(textarea).toContain("Textarea")
  })

  it("memuat ekspor Label dari label.tsx", () => {
    const label = fs.readFileSync(path.resolve("./src/components/ui/label.tsx"), "utf-8")
    expect(label).toContain("Label")
  })

  it("memuat ekspor Checkbox dari checkbox.tsx", () => {
    const checkbox = fs.readFileSync(path.resolve("./src/components/ui/checkbox.tsx"), "utf-8")
    expect(checkbox).toContain("Checkbox")
  })

  it("penanda gaya pada button.tsx: h-11 dan hover:bg-primary-hover", () => {
    const button = fs.readFileSync(path.resolve("./src/components/ui/button.tsx"), "utf-8")
    expect(button).toContain("h-11")
    expect(button).toContain("hover:bg-primary-hover")
  })

  it("penanda gaya pada card.tsx: rounded-xl", () => {
    const card = fs.readFileSync(path.resolve("./src/components/ui/card.tsx"), "utf-8")
    expect(card).toContain("rounded-xl")
  })

  it("penanda gaya pada badge.tsx: rounded-full", () => {
    const badge = fs.readFileSync(path.resolve("./src/components/ui/badge.tsx"), "utf-8")
    expect(badge).toContain("rounded-full")
  })

  it("penanda gaya pada select.tsx: h-11", () => {
    const select = fs.readFileSync(path.resolve("./src/components/ui/select.tsx"), "utf-8")
    expect(select).toContain("h-11")
  })
})