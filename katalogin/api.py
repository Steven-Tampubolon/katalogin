import os

from fastapi import FastAPI


def create_app(
    db_path: str | None = None, admin_token: str | None = None
) -> FastAPI:
    app = FastAPI()
    app.state.db_path = db_path or os.environ.get("KATALOGIN_DB", "katalogin.db")
    app.state.admin_token = admin_token or os.environ.get("KATALOGIN_ADMIN_TOKEN")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
