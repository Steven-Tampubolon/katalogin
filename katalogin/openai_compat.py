import base64
import time
from collections.abc import Callable

import httpx

from katalogin.llm import LLMClient, LLMError


_STATUS_LAYANAN_GAGAL = {500, 502, 503, 504}


class OpenAICompatClient(LLMClient):
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        *,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 60.0,
        max_percobaan: int = 3,
        tidur: Callable[[float], None] = time.sleep,
    ) -> None:
        if not api_key.strip():
            raise ValueError("API key LLM kosong")
        if not model.strip():
            raise ValueError("Nama model LLM kosong")

        base_url = base_url.strip()
        if not base_url.startswith(("http://", "https://")):
            raise ValueError("Alamat dasar LLM harus diawali http:// atau https://")

        self.model = model
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._transport = transport
        self._timeout = timeout
        self._max_percobaan = max_percobaan
        self._tidur = tidur

    def __repr__(self) -> str:
        return f"OpenAICompatClient(model={self.model}, base_url={self._base_url})"

    def complete(self, prompt: str) -> str:
        return self._kirim(prompt)

    def complete_dengan_gambar(self, prompt: str, gambar: bytes, mime: str) -> str:
        data = base64.b64encode(gambar).decode("ascii")
        return self._kirim(
            [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{data}"},
                },
            ]
        )

    def _kirim(self, isi: str | list[dict[str, object]]) -> str:
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": isi}],
        }

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
        pilihan = data.get("choices")
        if not isinstance(pilihan, list) or not pilihan:
            raise LLMError("Balasan AI kosong atau tidak valid")
        kandidat = pilihan[0]
        if not isinstance(kandidat, dict):
            raise LLMError("Balasan AI kosong atau tidak valid")
        pesan = kandidat.get("message")
        if not isinstance(pesan, dict):
            raise LLMError("Balasan AI kosong atau tidak valid")
        konten = pesan.get("content")
        if isinstance(konten, str):
            teks = konten
        elif isinstance(konten, list):
            teks = "".join(
                item["text"]
                for item in konten
                if isinstance(item, dict)
                and item.get("type") == "text"
                and isinstance(item.get("text"), str)
            )
        else:
            raise LLMError("Balasan AI kosong atau tidak valid")

        if not teks:
            raise LLMError("Balasan AI kosong atau tidak valid")
        return teks
