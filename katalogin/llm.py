import abc
import json
import logging

from katalogin.extract import ekstrak_teks
from katalogin.models import Product
from katalogin.textutil import rapikan_spasi, rapikan_teks

ALASAN_PENYEDIA_GAGAL = "penyedia_gagal"
ALASAN_RESPONS_TIDAK_VALID = "respons_tidak_valid"
BATAS_FIELD = 200
BATAS_FITUR_JUMLAH = 20
BATAS_FITUR_PANJANG = 100
CATATAN_ALASAN = {
    ALASAN_PENYEDIA_GAGAL: "Layanan AI gagal merespons; hasil dibuat dengan aturan biasa.",
    ALASAN_RESPONS_TIDAK_VALID: "Jawaban AI tidak dapat dibaca; hasil dibuat dengan aturan biasa.",
}
logger = logging.getLogger("katalogin.llm")

PROMPT_EKSTRAKSI = (
    "Ekstrak informasi produk dari teks supplier. Balas hanya satu objek JSON "
    "dengan kunci nama, merek, bahan, ukuran, warna, fungsi, dan fitur. "
    "Isi fitur dengan array string dan nilai yang tidak diketahui dengan null. "
    "Jangan menambahkan penjelasan.\n\n"
    "Teks supplier:\n{TEKS}"
)

PROMPT_FOTO = (
    "Baca foto produk dan ekstrak informasi yang terlihat. Balas hanya satu "
    "objek JSON dengan kunci nama, merek, bahan, ukuran, warna, fungsi, dan fitur. "
    "Isi fitur dengan array string dan nilai yang tidak terlihat jelas di foto "
    "dengan null. Jangan mengarang informasi dan jangan menambahkan penjelasan."
)


class LLMError(Exception):
    pass


class LLMClient(abc.ABC):
    @abc.abstractmethod
    def complete(self, prompt: str) -> str:
        ...

    def complete_dengan_gambar(self, prompt: str, gambar: bytes, mime: str) -> str:
        raise NotImplementedError("Klien ini tidak mendukung gambar")


class FakeLLM(LLMClient):
    def __init__(self, respons: str | Exception) -> None:
        self.respons = respons
        self.prompts: list[str] = []
        self.gambar: list[tuple[str, bytes, str]] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if isinstance(self.respons, Exception):
            raise self.respons
        return self.respons

    def complete_dengan_gambar(self, prompt: str, gambar: bytes, mime: str) -> str:
        self.gambar.append((prompt, gambar, mime))
        if isinstance(self.respons, Exception):
            raise self.respons
        return self.respons


def _nilai_teks(nilai: object) -> str | None:
    if not isinstance(nilai, str):
        return None
    teks = rapikan_teks(nilai)
    if len(teks) > BATAS_FIELD:
        return None
    return teks


def _merek_dalam_batas(merek: object) -> str | None:
    if not isinstance(merek, str):
        return None
    cleaned = rapikan_spasi(merek)
    if len(cleaned) > BATAS_FIELD:
        return None
    return cleaned


def _produk_dari_respons(respons: str) -> Product | None:
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
        return None

    # Cek panjang nama setelah dirapikan
    nama_bersih = rapikan_teks(nama)
    if len(nama_bersih) > BATAS_FIELD:
        return None

    merek = data.get("merek")
    bahan = data.get("bahan")
    ukuran = data.get("ukuran")
    warna = data.get("warna")
    fungsi = data.get("fungsi")
    fitur = data.get("fitur")

    merek = _merek_dalam_batas(data.get("merek"))
    bahan = _nilai_teks(data.get("bahan"))
    ukuran = _nilai_teks(data.get("ukuran"))
    warna = _nilai_teks(data.get("warna"))
    fungsi = _nilai_teks(data.get("fungsi"))
    fitur = _rapikan_fitur(data.get("fitur"))

    return Product(
        nama=nama_bersih,
        merek=merek,
        bahan=bahan,
        ukuran=ukuran,
        warna=warna,
        fungsi=fungsi,
        fitur=fitur,
    )


def _rapikan_fitur(fitur: object) -> list[str]:
    if not isinstance(fitur, list) or not all(isinstance(item, str) for item in fitur):
        return []
    fitur_bersih = []
    for item in fitur:
        item_tersih = rapikan_teks(item)
        if len(item_tersih) <= BATAS_FITUR_PANJANG:
            fitur_bersih.append(item_tersih)
    return fitur_bersih[:BATAS_FITUR_JUMLAH]


def coba_ekstrak_dengan_llm(teks: str, client: LLMClient) -> Product | None:
    return coba_ekstrak_dengan_llm_rinci(teks, client)[0]


def coba_ekstrak_dengan_llm_rinci(teks: str, client: LLMClient) -> tuple[Product | None, str | None]:
    prompt = PROMPT_EKSTRAKSI.replace("{TEKS}", teks)
    try:
        respons = client.complete(prompt)
    except Exception as galat:
        logger.warning("Penyedia AI gagal: %s", type(galat).__name__)
        return (None, ALASAN_PENYEDIA_GAGAL)
    produk = _produk_dari_respons(respons)
    if produk is None:
        return (None, ALASAN_RESPONS_TIDAK_VALID)
    return (produk, None)


def ekstrak_dengan_llm(teks: str, client: LLMClient) -> Product:
    return coba_ekstrak_dengan_llm(teks, client) or ekstrak_teks(teks)


def ekstrak_dari_gambar(gambar: bytes, mime: str, client: LLMClient) -> Product:
    respons = client.complete_dengan_gambar(PROMPT_FOTO, gambar, mime)
    produk = _produk_dari_respons(respons)
    if produk is None:
        raise ValueError("Gagal membaca produk dari gambar")
    return produk
