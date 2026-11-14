from katalogin.api import create_app


def test_health_mengembalikan_status_ok(klien) -> None:
    respons = klien.get("/health")

    assert respons.status_code == 200
    assert respons.json() == {"status": "ok"}


def test_create_app_menyimpan_jalur_database_yang_diberikan(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)

    app = create_app(db_path="x.db")

    assert app.state.db_path == "x.db"


def test_create_app_mengambil_jalur_database_dari_lingkungan(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("KATALOGIN_DB", "dari-env.db")

    app = create_app()

    assert app.state.db_path == "dari-env.db"


def test_create_app_tidak_memiliki_token_admin_bila_lingkungan_kosong(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("KATALOGIN_ADMIN_TOKEN", raising=False)

    app = create_app()

    assert app.state.admin_token is None
