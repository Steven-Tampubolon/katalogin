import abc
import json

from katalogin.extract import ekstrak_teks
from katalogin.models import Product
from katalogin.textutil import rapikan_spasi, rapikan_teks

PROMPT_EKSTRAKSI = (
    "Ekstrak informasi produk dari teks supplier. Balas hanya satu objek JSON "
    "dengan kunci nama, merek, bahan, ukuran, warna, fungsi, dan fitur. "
    "Isi fitur dengan array string dan nilai yang tidak diketahui dengan null. "
    "Jangan menambahkan penjelasan.\n\n"
    "Teks supplier:\n{TEKS}"
)


class LLMClient(abc.ABC):
    @abc.abstractmethod
    def complete(self, prompt: str) -> str:
        ...


class FakeLLM(LLMClient):
    def __init__(self, respons: str | Exception) -> None:
        self.respons = respons
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if isinstance(self.respons, Exception):
            raise self.respons
        return self.respons


def _nilai_teks(nilai: object) -> str | None:
    if not isinstance(nilai, str):
        return None
    return rapikan_teks(nilai)


def ekstrak_dengan_llm(teks: str, client: LLMClient) -> Product:
    prompt = PROMPT_EKSTRAKSI.replace("{TEKS}", teks)
    try:
        respons = client.complete(prompt)
    except Exception:
        return ekstrak_teks(teks)

    try:
        awal = respons.find("{")
        akhir = respons.rfind("}")
        if awal < 0 or akhir < awal:
            raise ValueError
        data = json.loads(respons[awal : akhir + 1])
        if not isinstance(data, dict):
            raise ValueError
        nama = data.get("nama")
        if not isinstance(nama, str) or not nama.strip():
            raise ValueError
    except (AttributeError, TypeError, ValueError):
        return ekstrak_teks(teks)

    merek = data.get("merek")
    fitur = data.get("fitur")
    return Product(
        nama=rapikan_teks(nama),
        merek=rapikan_spasi(merek) if isinstance(merek, str) else None,
        bahan=_nilai_teks(data.get("bahan")),
        ukuran=_nilai_teks(data.get("ukuran")),
        warna=_nilai_teks(data.get("warna")),
        fungsi=_nilai_teks(data.get("fungsi")),
        fitur=(
            [rapikan_teks(item) for item in fitur]
            if isinstance(fitur, list)
            and all(isinstance(item, str) for item in fitur)
            else []
        ),
    )
