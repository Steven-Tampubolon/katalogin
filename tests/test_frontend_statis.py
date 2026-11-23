import os
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient
from katalogin.api import create_app


def _buat_folder_frontend(tmp_path: str) -> str:
    folder = os.path.join(tmp_path, "frontend", "dist")
    os.makedirs(folder, exist_ok=True)
    index_path = os.path.join(folder, "index.html")
    with open(index_path, "w") as f:
        f.write("<html>ok</html>")
    assets_folder = os.path.join(folder, "assets")
    os.makedirs(assets_folder, exist_ok=True)
    js_path = os.path.join(assets_folder, "app.js")
    with open(js_path, "w") as f:
        f.write("//# sourceMappingURL=data:application/javascript;base64,AAAA")
    return folder


def test_frontend_statis_dengan_index_html(tmp_path) -> None:
    folder = _buat_folder_frontend(tmp_path)
    klien = TestClient(
        create_app(frontend_dir=folder, db_path=str(tmp_path / "t.db"), admin_token="token-uji")
    )
    respons = klien.get("/")
    assert respons.status_code == 200
    assert "ok" in respons.text
    respons_js = klien.get("/assets/app.js")
    assert respons_js.status_code == 200
    respons_health = klien.get("/health")
    assert respons_health.status_code == 200
    assert respons_health.json() == {"status": "ok"}
    respons_kredit_dengan = klien.get("/kredit", headers={"X-User-Id": "u1"})
    assert respons_kredit_dengan.status_code == 200
    respons_kredit_tanpa = klien.get("/kredit")
    assert respons_kredit_tanpa.status_code == 401


def test_frontend_tanpa_folder_index_404(tmp_path) -> None:
    folder = os.path.join(tmp_path, "empty_frontend")
    os.makedirs(folder, exist_ok=True)
    klien = TestClient(
        create_app(frontend_dir=folder, db_path=str(tmp_path / "t.db"), admin_token="token-uji")
    )
    respons = klien.get("/")
    assert respons.status_code == 404


def test_frontend_tanpa_parameter_dengan_default_200(tmp_path) -> None:
    # Tanpa parameter frontend_dir, default ke frontend/dist yang ada
    klien = TestClient(
        create_app(db_path=str(tmp_path / "t.db"), admin_token="token-uji")
    )
    respons = klien.get("/")
    assert respons.status_code == 200


def test_frontend_dengan_dir_tidak_ada_404(tmp_path) -> None:
    folder = os.path.join(tmp_path, "nonexistent")
    klien = TestClient(
        create_app(frontend_dir=folder, db_path=str(tmp_path / "t.db"), admin_token="token-uji")
    )
    respons = klien.get("/")
    assert respons.status_code == 404


def test_frontend_dengan_index_tapi_tidak_ada_file_404(tmp_path) -> None:
    folder = os.path.join(tmp_path, "frontend_dengan_tidak_ada_index")
    os.makedirs(folder, exist_ok=True)
    klien = TestClient(
        create_app(frontend_dir=folder, db_path=str(tmp_path / "t.db"), admin_token="token-uji")
    )
    respons = klien.get("/")
    assert respons.status_code == 404