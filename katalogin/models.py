from dataclasses import dataclass, field


@dataclass
class Product:
    nama: str
    merek: str | None = None
    bahan: str | None = None
    ukuran: str | None = None
    warna: str | None = None
    fungsi: str | None = None
    fitur: list[str] = field(default_factory=list)
