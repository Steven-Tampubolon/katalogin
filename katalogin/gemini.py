import base64
import time
from collections.abc import Callable

import httpx

from katalogin.llm import LLMClient, LLMError

_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent"
)
_STATUS_LAYANAN_GAGAL = {500, 502, 503, 504}


class GeminiClient(LLMClient):
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.6-flash",
        *,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 30.0,
        max_percobaan: int = 3,
        tidur: Callable[[float], None] = time.sleep,
    ) -> None:
        if not api_key.strip():
            raise ValueError("API key Gemini kosong")
        self.model = model
        self._api_key = api_key
        self._transport = transport
        self._timeout = timeout
        self._max_percobaan = max_percobaan
        self._tidur = tidur

    def __repr__(self) -> str:
        return f"GeminiClient(model={self.model})"

    def complete(self, prompt: str) -> str:
        return self._kirim([{"text": prompt}])

    def complete_dengan_gambar(self, prompt: str, gambar: bytes, mime: str) -> str:
        return self._kirim(
            [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": mime,
                        "data": base64.b64encode(gambar).decode("ascii"),
                    }
                },
            ]
        )

    def _kirim(self, bagian: list[dict]) -> str:
        url = _URL.format(model=self.model)
        headers = {
            "x-goog-api-key": self._api_key,
            "Content-Type": "application/json",
        }
        payload = {"contents": [{"parts": bagian}]}

        with httpx.Client(
            transport=self._transport,
            timeout=self._timeout,
        ) as client:
            for percobaan in range(1, self._max_percobaan + 1):
                if percobaan > 1:
                    self._tidur(percobaan - 1)
                try:
                    respons = client.post(url, headers=headers, json=payload)
                except httpx.TimeoutException:
                    if percobaan < self._max_percobaan:
                        continue
                    raise LLMError("Waktu tunggu AI habis") from None
                except httpx.TransportError:
                    if percobaan < self._max_percobaan:
                        continue
                    raise LLMError("Koneksi ke AI gagal") from None

                status = respons.status_code
                if status == 200:
                    return self._teks_dari_respons(respons)
                if status == 429:
                    if percobaan < self._max_percobaan:
                        continue
                    raise LLMError(
                        "Kuota atau batas laju AI terlampaui (HTTP 429)"
                    ) from None
                if status in _STATUS_LAYANAN_GAGAL:
                    if percobaan < self._max_percobaan:
                        continue
                    raise LLMError(
                        f"Layanan AI tidak tersedia (HTTP {status})"
                    ) from None
                raise LLMError(
                    f"Permintaan ke AI ditolak (HTTP {status})"
                ) from None

        raise LLMError("Balasan AI kosong atau tidak valid")

    def _teks_dari_respons(self, respons: httpx.Response) -> str:
        try:
            data = respons.json()
        except ValueError:
            raise LLMError("Balasan AI kosong atau tidak valid") from None

        if not isinstance(data, dict):
            raise LLMError("Balasan AI kosong atau tidak valid")
        kandidat = data.get("candidates")
        if not isinstance(kandidat, list) or not kandidat:
            raise LLMError("Balasan AI kosong atau tidak valid")
        isi = kandidat[0]
        if not isinstance(isi, dict):
            raise LLMError("Balasan AI kosong atau tidak valid")
        konten = isi.get("content")
        if not isinstance(konten, dict):
            raise LLMError("Balasan AI kosong atau tidak valid")
        bagian = konten.get("parts")
        if not isinstance(bagian, list):
            raise LLMError("Balasan AI kosong atau tidak valid")

        teks = "".join(
            item["text"]
            for item in bagian
            if isinstance(item, dict) and isinstance(item.get("text"), str)
        )
        if not teks:
            raise LLMError("Balasan AI kosong atau tidak valid")
        return teks
