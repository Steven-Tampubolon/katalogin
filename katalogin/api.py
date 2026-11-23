import dataclasses
import hmac
import os
import re
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, Field
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from katalogin import credits, db, history, service
from katalogin.credits import KreditTidakCukup
from katalogin.csvio import baca_csv, ekspor_csv
from katalogin.extract import ekstrak_teks
from katalogin.gambar import decode_base64, deteksi_mime
from katalogin.llm import (
    CATATAN_ALASAN,
    LLMClient,
    LLMError,
    coba_ekstrak_dengan_llm_rinci,
    ekstrak_dari_gambar,
)
from katalogin.llm_config import buat_klien_dari_env
from katalogin.models import Product


POLA_USER_ID = re.compile(r"^[A-Za-z0-9_.@-]{1,64}$")
BATAS_CONTENT_LENGTH = 1_000_000


class ModelProduk(BaseModel):
    nama: str = Field(max_length=200)
    merek: str | None = Field(default=None, max_length=200)
    bahan: str | None = Field(default=None, max_length=200)
    ukuran: str | None = Field(default=None, max_length=200)
    warna: str | None = Field(default=None, max_length=200)
    fungsi: str | None = Field(default=None, max_length=200)
    fitur: list[Annotated[str, Field(max_length=100)]] = Field(
        default_factory=list, max_length=20
    )


class ModelGenerate(BaseModel):
    platform: str = Field(max_length=30)
    tone: str = Field(default="kasual", max_length=30)
    produk: ModelProduk | None = None
    teks: str | None = Field(default=None, max_length=20000)
    gunakan_ai: bool = False


class ModelGenerateFoto(BaseModel):
    platform: str = Field(max_length=30)
    tone: str = Field(default="kasual", max_length=30)
    gambar_base64: str = Field(max_length=6800000)


class ModelGenerateCSV(BaseModel):
    platform: str = Field(max_length=30)
    tone: str = Field(default="kasual", max_length=30)
    csv: str = Field(max_length=100000)


class ModelAdminKredit(BaseModel):
    user_id: str = Field(max_length=64)
    jumlah: int = Field(ge=1, le=100000)


def ambil_user(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> str:
    if x_user_id is None:
        raise HTTPException(
            status_code=401, detail="Header X-User-Id wajib diisi"
        )
    if POLA_USER_ID.fullmatch(x_user_id) is None:
        raise HTTPException(status_code=400, detail="X-User-Id tidak valid")
    return x_user_id


class BatasBodyMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        batas: int,
        batas_per_jalur: dict[str, int] | None = None,
    ) -> None:
        self.app = app
        self.batas = batas
        self.batas_per_jalur = batas_per_jalur or {}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        content_length = Headers(scope=scope).get("content-length")
        try:
            panjang_body = int(content_length) if content_length is not None else 0
        except ValueError:
            panjang_body = 0
        batas = self.batas_per_jalur.get(scope["path"], self.batas)
        if panjang_body > batas:
            await self._tolak(scope, receive, send)
            return

        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            if message["type"] != "http.request":
                continue

            chunk = message.get("body", b"")
            if len(body) + len(chunk) > batas:
                await self._tolak(scope, receive, send)
                return
            body.extend(chunk)
            if not message.get("more_body", False):
                break

        body_sent = False

        async def receive_body() -> Message:
            nonlocal body_sent
            if body_sent:
                return {"type": "http.disconnect"}
            body_sent = True
            return {"type": "http.request", "body": bytes(body), "more_body": False}

        await self.app(scope, receive_body, send)

    async def _tolak(self, scope: Scope, receive: Receive, send: Send) -> None:
        respons = JSONResponse(
            status_code=413,
            content={"detail": "Permintaan terlalu besar"},
        )
        await respons(scope, receive, send)


def create_app(
    db_path: str | None = None,
    admin_token: str | None = None,
    llm_client: LLMClient | None = None,
    frontend_dir: str | None = None,
) -> FastAPI:
    app = FastAPI()
    app.state.db_path = db_path or os.environ.get("KATALOGIN_DB", "katalogin.db")
    app.state.admin_token = admin_token or os.environ.get("KATALOGIN_ADMIN_TOKEN")
    app.state.llm_client = (
        llm_client if llm_client is not None else buat_klien_dari_env()
    )
    db.init_db(app.state.db_path)
    app.add_middleware(
        BatasBodyMiddleware,
        batas=BATAS_CONTENT_LENGTH,
        batas_per_jalur={"/generate/foto": 7_000_000},
    )

    if frontend_dir is None:
        frontend_dir = os.environ.get("KATALOGIN_FRONTEND_DIR")
    if not frontend_dir:
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        frontend_dir = os.path.join(repo_root, "frontend", "dist")

    if frontend_dir and os.path.isdir(frontend_dir) and os.path.isfile(
        os.path.join(frontend_dir, "index.html")
    ):
        with open(os.path.join(frontend_dir, "index.html")) as f:
            index_content = f.read()

        @app.get("/", include_in_schema=False)
        def serve_index():
            return Response(content=index_content, media_type="text/html")

        @app.get("/assets/{path:path}", include_in_schema=False)
        def serve_assets(path: str):
            asset_path = os.path.join(frontend_dir, "assets", path)
            if os.path.isfile(asset_path):
                with open(asset_path, "rb") as f:
                    asset_content = f.read()
                return Response(content=asset_content, media_type="application/javascript")
            raise HTTPException(status_code=404)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/kredit")
    def kredit(user_id: str = Depends(ambil_user)) -> dict[str, str | int]:
        koneksi = db.buka(app.state.db_path)
        try:
            with db.transaksi(koneksi):
                credits.pastikan_pengguna(koneksi, user_id, db.sekarang())
                saldo = credits.saldo(koneksi, user_id)
        finally:
            koneksi.close()

        return {"user_id": user_id, "kredit": saldo}

    @app.post("/generate")
    def generate(
        permintaan: ModelGenerate,
        user_id: str = Depends(ambil_user),
    ) -> dict[str, object]:
        if permintaan.gunakan_ai and permintaan.produk is not None:
            raise HTTPException(
                status_code=400,
                detail="gunakan_ai hanya berlaku untuk 'teks'",
            )

        ekstraksi: str | None = None
        if permintaan.produk is not None:
            if permintaan.teks is not None:
                raise HTTPException(
                    status_code=400,
                    detail="Isi tepat salah satu dari 'produk' atau 'teks'",
                )
            produk = Product(
                nama=permintaan.produk.nama,
                merek=permintaan.produk.merek,
                bahan=permintaan.produk.bahan,
                ukuran=permintaan.produk.ukuran,
                warna=permintaan.produk.warna,
                fungsi=permintaan.produk.fungsi,
                fitur=permintaan.produk.fitur,
            )
        elif permintaan.teks is not None:
            if permintaan.gunakan_ai:
                llm_client = app.state.llm_client
                if llm_client is None:
                    raise HTTPException(
                        status_code=503,
                        detail="Layanan AI belum dikonfigurasi",
                    )

                koneksi = db.buka(app.state.db_path)
                try:
                    saldo = credits.saldo_efektif(koneksi, user_id)
                finally:
                    koneksi.close()
                if saldo < 1:
                    raise HTTPException(
                        status_code=402,
                        detail=f"Kredit tidak cukup: butuh 1, tersisa {saldo}",
                    )

                produk_ai, alasan = coba_ekstrak_dengan_llm_rinci(permintaan.teks, llm_client)
                if produk_ai is not None:
                    produk = produk_ai
                    ekstraksi = "ai"
                else:
                    try:
                        produk = ekstrak_teks(permintaan.teks)
                    except ValueError as galat:
                        raise HTTPException(status_code=400, detail=str(galat)) from galat
                    ekstraksi = "aturan"
            else:
                try:
                    produk = ekstrak_teks(permintaan.teks)
                except ValueError as galat:
                    raise HTTPException(status_code=400, detail=str(galat)) from galat
        else:
            raise HTTPException(
                status_code=400,
                detail="Isi tepat salah satu dari 'produk' atau 'teks'",
            )

        try:
            proses = service.proses(
                db_path=app.state.db_path,
                user_id=user_id,
                daftar_produk=[produk],
                platform=permintaan.platform,
                tone=permintaan.tone,
            )
        except KreditTidakCukup as galat:
            raise HTTPException(status_code=402, detail=str(galat)) from galat
        except ValueError as galat:
            raise HTTPException(status_code=400, detail=str(galat)) from galat

        respons: dict[str, object] = {
            "id": proses.ids[0],
            "hasil": dataclasses.asdict(proses.hasil[0]),
            "sisa_kredit": proses.sisa_kredit,
        }
        if ekstraksi is not None:
            respons["ekstraksi"] = ekstraksi
            if ekstraksi == "aturan":
                respons["alasan_fallback"] = alasan
                respons["catatan_ai"] = CATATAN_ALASAN[alasan]
        return respons

    @app.post("/generate/foto")
    def generate_foto(
        permintaan: ModelGenerateFoto,
        user_id: str = Depends(ambil_user),
    ) -> dict[str, object]:
        llm_client = app.state.llm_client
        if llm_client is None:
            raise HTTPException(
                status_code=503,
                detail="Layanan AI belum dikonfigurasi",
            )

        try:
            gambar = decode_base64(permintaan.gambar_base64)
            mime = deteksi_mime(gambar)
        except ValueError as galat:
            raise HTTPException(status_code=400, detail=str(galat)) from galat

        koneksi = db.buka(app.state.db_path)
        try:
            saldo = credits.saldo_efektif(koneksi, user_id)
        finally:
            koneksi.close()
        if saldo < 1:
            raise HTTPException(
                status_code=402,
                detail=f"Kredit tidak cukup: butuh 1, tersisa {saldo}",
            )

        try:
            produk = ekstrak_dari_gambar(gambar, mime, llm_client)
        except LLMError as galat:
            raise HTTPException(
                status_code=502,
                detail=f"Layanan AI gagal: {galat}",
            ) from galat
        except ValueError as galat:
            raise HTTPException(status_code=422, detail=str(galat)) from galat
        except NotImplementedError as galat:
            raise HTTPException(
                status_code=503,
                detail="Layanan AI belum mendukung gambar",
            ) from galat

        try:
            proses = service.proses(
                db_path=app.state.db_path,
                user_id=user_id,
                daftar_produk=[produk],
                platform=permintaan.platform,
                tone=permintaan.tone,
            )
        except KreditTidakCukup as galat:
            raise HTTPException(status_code=402, detail=str(galat)) from galat
        except ValueError as galat:
            raise HTTPException(status_code=400, detail=str(galat)) from galat

        return {
            "id": proses.ids[0],
            "hasil": dataclasses.asdict(proses.hasil[0]),
            "sisa_kredit": proses.sisa_kredit,
            "ekstraksi": "foto",
            "produk_terbaca": dataclasses.asdict(produk),
        }

    @app.post("/generate/csv")
    def generate_csv(
        permintaan: ModelGenerateCSV,
        user_id: str = Depends(ambil_user),
    ) -> dict[str, object]:
        try:
            daftar_produk = baca_csv(permintaan.csv)
            proses = service.proses(
                db_path=app.state.db_path,
                user_id=user_id,
                daftar_produk=daftar_produk,
                platform=permintaan.platform,
                tone=permintaan.tone,
            )
        except KreditTidakCukup as galat:
            raise HTTPException(status_code=402, detail=str(galat)) from galat
        except ValueError as galat:
            raise HTTPException(status_code=400, detail=str(galat)) from galat

        return {
            "ids": proses.ids,
            "hasil": [dataclasses.asdict(item) for item in proses.hasil],
            "csv": ekspor_csv(proses.hasil),
            "sisa_kredit": proses.sisa_kredit,
        }

    @app.get("/riwayat")
    def daftar_riwayat(
        user_id: str = Depends(ambil_user),
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
    ) -> dict[str, object]:
        koneksi = db.buka(app.state.db_path)
        try:
            total = history.hitung(koneksi, user_id)
            item = history.daftar(koneksi, user_id, limit, offset)
        finally:
            koneksi.close()

        return {"total": total, "item": item}

    @app.get("/riwayat/{riwayat_id}")
    def detail_riwayat(
        riwayat_id: int,
        user_id: str = Depends(ambil_user),
    ) -> dict[str, object]:
        koneksi = db.buka(app.state.db_path)
        try:
            item = history.ambil(koneksi, user_id, riwayat_id)
        finally:
            koneksi.close()

        if item is None:
            raise HTTPException(status_code=404, detail="Riwayat tidak ditemukan")
        return item

    @app.post("/admin/kredit")
    def admin_kredit(
        permintaan: ModelAdminKredit,
        x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
    ) -> dict[str, str | int]:
        token_server = app.state.admin_token
        if (
            token_server is None
            or not x_admin_token
            or not hmac.compare_digest(
                token_server.encode("utf-8"), x_admin_token.encode("utf-8")
            )
        ):
            raise HTTPException(status_code=403, detail="Token admin tidak valid")

        if POLA_USER_ID.fullmatch(permintaan.user_id) is None:
            raise HTTPException(status_code=400, detail="user_id tidak valid")

        koneksi = db.buka(app.state.db_path)
        try:
            with db.transaksi(koneksi):
                waktu = db.sekarang()
                credits.pastikan_pengguna(koneksi, permintaan.user_id, waktu)
                saldo = credits.tambah(
                    koneksi, permintaan.user_id, permintaan.jumlah, "topup", waktu
                )
        finally:
            koneksi.close()

        return {"user_id": permintaan.user_id, "kredit": saldo}

    return app
