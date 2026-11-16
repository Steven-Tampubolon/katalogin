import base64
import os
from collections.abc import Mapping

import httpx


ALAMAT_API_BAWAAN = "http://127.0.0.1:8000"
GALAT_URL = "KATALOGIN_API_URL harus diawali http:// atau https://"


class ApiError(Exception):
    def __init__(self, status: int, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail


def buat_http_dari_env(env: Mapping[str, str] | None = None) -> httpx.Client:
    if env is None:
        env = os.environ

    alamat = env.get("KATALOGIN_API_URL", ALAMAT_API_BAWAAN).strip().rstrip("/")
    if not alamat.startswith(("http://", "https://")):
        raise ValueError(GALAT_URL)

    return httpx.Client(base_url=alamat, timeout=120.0)


class KlienApi:
    def __init__(self, http: httpx.Client, user_id: str) -> None:
        self.http = http
        self.user_id = user_id

    def _headers(self) -> dict[str, str]:
        return {"X-User-Id": self.user_id}

    def _permintaan(
        self,
        metode: str,
        path: str,
        *,
        json_body: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        try:
            respons = self.http.request(
                metode,
                path,
                headers=self._headers(),
                json=json_body,
                params=params,
            )
        except httpx.TimeoutException as galat:
            raise ApiError(0, "Server API tidak menjawab (waktu habis)") from galat
        except httpx.TransportError as galat:
            raise ApiError(0, "Tidak bisa terhubung ke server API") from galat

        if respons.status_code >= 400:
            raise ApiError(respons.status_code, self._detail_galat(respons))

        return respons.json()

    @staticmethod
    def _detail_galat(respons: httpx.Response) -> str:
        try:
            data = respons.json()
        except ValueError:
            return f"Galat server (HTTP {respons.status_code})"

        detail = data.get("detail") if isinstance(data, dict) else None
        if not isinstance(detail, str):
            return "Masukan tidak valid"
        return detail

    def kredit(self) -> int:
        respons = self._permintaan("GET", "/kredit")
        return respons["kredit"]

    def generate_teks(
        self,
        teks: str,
        platform: str,
        tone: str,
        gunakan_ai: bool = False,
    ) -> dict:
        return self._permintaan(
            "POST",
            "/generate",
            json_body={
                "platform": platform,
                "tone": tone,
                "teks": teks,
                "gunakan_ai": gunakan_ai,
            },
        )

    def generate_foto(
        self,
        gambar: bytes,
        platform: str,
        tone: str,
    ) -> dict:
        return self._permintaan(
            "POST",
            "/generate/foto",
            json_body={
                "platform": platform,
                "tone": tone,
                "gambar_base64": base64.b64encode(gambar).decode("ascii"),
            },
        )

    def generate_csv(self, csv_teks: str, platform: str, tone: str) -> dict:
        return self._permintaan(
            "POST",
            "/generate/csv",
            json_body={
                "platform": platform,
                "tone": tone,
                "csv": csv_teks,
            },
        )

    def riwayat(self, limit: int = 20, offset: int = 0) -> dict:
        return self._permintaan(
            "GET",
            "/riwayat",
            params={"limit": limit, "offset": offset},
        )

    def riwayat_item(self, riwayat_id: int) -> dict:
        return self._permintaan("GET", f"/riwayat/{riwayat_id}")
