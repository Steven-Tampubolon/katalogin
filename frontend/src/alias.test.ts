// @vitest-environment node
import { describe, it, expect } from "vitest"
import { cn } from "@/lib/utils"

describe("Tugas 1: Alias dan utilitas", () => {
  it("cn menggabungkan kelas", () => {
    expect(cn("a", "b")).toBe("a b")
  })
})