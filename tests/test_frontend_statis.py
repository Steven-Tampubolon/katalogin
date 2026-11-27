"""Tes penyajian build frontend oleh API (pengganti tests/test_frontend_statis.py).

Menjaga dua hal yang lolos dari tes sebelumnya: tipe konten setiap jenis aset (CSS yang dikirim sebagai
JavaScript ditolak peramban, halaman tampil tanpa gaya) dan penolakan path traversal. Semua tes membuat
folder sendiri di tmp_path; tidak ada yang bergantung pada frontend/dist yang dibangun di repo.
"""
import os

from fastapi.testclient import TestClient

from katalogin.api import create_app


def _buat_dist(tmp_path):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text(
        '<!doctype html><html><head><link rel="stylesheet" href="/assets/app.css"></head>'
        "<body>ok</body></html>",
        encoding="utf-8",
    )
    (dist / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")
    (dist / "assets" / "app.css").write_text("body{color:red}", encoding="utf-8")
    (dist / "assets" / "ikon.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>", encoding="utf-8")
    (dist / "assets" / "huruf.woff2").write_bytes(b"wOF2\x00\x01\x00\x00")
    (dist / "favicon.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>", encoding="utf-8")
    (tmp_path / "rahasia.txt").write_text("TOP-SECRET", encoding="utf-8")
    return dist


def _klien(tmp_path, **kwargs):
    dist = _buat_dist(tmp_path)
    app = create_app(
        frontend_dir=str(dist),
        db_path=str(tmp_path / "t.db"),
        admin_token="token-uji",
        **kwargs,
    )
    return TestClient(app)


def _tipe(respons):
    return respons.headers["content-type"].split(";")[0].strip().lower()


def test_frontend_statis_dengan_index_html(tmp_path) -> None:
    klien = _klien(tmp_path)
    respons = klien.get("/")
    assert respons.status_code == 200
    assert "ok" in respons.text
    assert klien.get("/assets/app.js").status_code == 200
    respons_health = klien.get("/health")
    assert respons_health.status_code == 200
    assert respons_health.json() == {"status": "ok"}
    assert klien.get("/kredit", headers={"X-User-Id": "u1"}).status_code == 200
    assert klien.get("/kredit").status_code == 401


def test_index_disajikan_sebagai_html(tmp_path) -> None:
    respons = _klien(tmp_path).get("/")
    assert _tipe(respons) == "text/html"


def test_css_disajikan_sebagai_text_css(tmp_path) -> None:
    respons = _klien(tmp_path).get("/assets/app.css")
    assert respons.status_code == 200
    assert _tipe(respons) == "text/css"


def test_js_disajikan_sebagai_javascript(tmp_path) -> None:
    respons = _klien(tmp_path).get("/assets/app.js")
    assert respons.status_code == 200
    assert "javascript" in _tipe(respons)


def test_svg_disajikan_sebagai_gambar_svg(tmp_path) -> None:
    respons = _klien(tmp_path).get("/assets/ikon.svg")
    assert respons.status_code == 200
    assert _tipe(respons) == "image/svg+xml"


def test_font_tidak_disajikan_sebagai_javascript_atau_teks(tmp_path) -> None:
    respons = _klien(tmp_path).get("/assets/huruf.woff2")
    assert respons.status_code == 200
    tipe = _tipe(respons)
    assert "javascript" not in tipe
    assert tipe not in ("text/html", "text/plain", "text/css")


def test_berkas_di_akar_dist_ikut_disajikan(tmp_path) -> None:
    respons = _klien(tmp_path).get("/favicon.svg")
    assert respons.status_code == 200
    assert _tipe(respons) == "image/svg+xml"


def test_path_traversal_ditolak(tmp_path) -> None:
    klien = _klien(tmp_path)
    for jalur in (
        "/assets/..%2f..%2frahasia.txt",
        "/assets/../../rahasia.txt",
        "/..%2frahasia.txt",
        "/assets/%2e%2e/%2e%2e/rahasia.txt",
    ):
        respons = klien.get(jalur)
        assert "TOP-SECRET" not in respons.text, jalur


def test_jalur_tak_dikenal_tetap_404(tmp_path) -> None:
    assert _klien(tmp_path).get("/tidak-ada").status_code == 404


def test_frontend_dari_variabel_lingkungan(tmp_path, monkeypatch) -> None:
    dist = _buat_dist(tmp_path)
    monkeypatch.setenv("KATALOGIN_FRONTEND_DIR", str(dist))
    klien = TestClient(create_app(db_path=str(tmp_path / "t.db"), admin_token="token-uji"))
    respons = klien.get("/")
    assert respons.status_code == 200
    assert "ok" in respons.text


def test_frontend_tanpa_folder_index_404(tmp_path) -> None:
    folder = os.path.join(tmp_path, "empty_frontend")
    os.makedirs(folder, exist_ok=True)
    klien = TestClient(
        create_app(frontend_dir=folder, db_path=str(tmp_path / "t.db"), admin_token="token-uji")
    )
    assert klien.get("/").status_code == 404


def test_frontend_dengan_dir_tidak_ada_404(tmp_path) -> None:
    folder = os.path.join(tmp_path, "nonexistent")
    klien = TestClient(
        create_app(frontend_dir=folder, db_path=str(tmp_path / "t.db"), admin_token="token-uji")
    )
    assert klien.get("/").status_code == 404
