import dataclasses
import os
import re

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from katalogin import credits, db, service
from katalogin.credits import KreditTidakCukup
from katalogin.extract import ekstrak_teks
from katalogin.models import Product


POLA_USER_ID = re.compile(r"^[A-Za-z0-9_.@-]{1,64}$")


class ModelProduk(BaseModel):
    nama: str
    merek: str | None = None
    bahan: str | None = None
    ukuran: str | None = None
    warna: str | None = None
    fungsi: str | None = None
    fitur: list[str] = Field(default_factory=list)


class ModelGenerate(BaseModel):
    platform: str
    tone: str = "kasual"
    produk: ModelProduk | None = None
    teks: str | None = None


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


def create_app(
    db_path: str | None = None, admin_token: str | None = None
) -> FastAPI:
    app = FastAPI()
    app.state.db_path = db_path or os.environ.get("KATALOGIN_DB", "katalogin.db")
    app.state.admin_token = admin_token or os.environ.get("KATALOGIN_ADMIN_TOKEN")
    db.init_db(app.state.db_path)

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
            produk = ekstrak_teks(permintaan.teks)
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

        return {
            "id": proses.ids[0],
            "hasil": dataclasses.asdict(proses.hasil[0]),
            "sisa_kredit": proses.sisa_kredit,
        }

    return app
