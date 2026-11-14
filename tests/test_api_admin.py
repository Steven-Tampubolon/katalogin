from fastapi.testclient import TestClient

from katalogin.api import create_app


def test_admin_kredit_memberikan_kredit_gratis_dan_topup(klien) -> None:
    respons = klien.post(
        "/admin/kredit",
        headers={"X-Admin-Token": "token-uji"},
        json={"user_id": "andi", "jumlah": 10},
    )

    assert respons.status_code == 200
    assert respons.json() == {"user_id": "andi", "kredit": 15}


def test_admin_kredit_menolak_token_salah(klien) -> None:
    respons = klien.post(
        "/admin/kredit",
        headers={"X-Admin-Token": "token-salah"},
        json={"user_id": "andi", "jumlah": 10},
    )

    assert respons.status_code == 403
    assert respons.json() == {"detail": "Token admin tidak valid"}


def test_admin_kredit_menolak_header_token_kosong(klien) -> None:
    respons = klien.post(
        "/admin/kredit",
        headers={"X-Admin-Token": ""},
        json={"user_id": "andi", "jumlah": 10},
    )

    assert respons.status_code == 403
    assert respons.json() == {"detail": "Token admin tidak valid"}


def test_admin_kredit_menolak_tanpa_header_token(klien) -> None:
    respons = klien.post(
        "/admin/kredit",
        json={"user_id": "andi", "jumlah": 10},
    )

    assert respons.status_code == 403
    assert respons.json() == {"detail": "Token admin tidak valid"}


def test_admin_kredit_menolak_token_server_yang_tidak_dikonfigurasi(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.delenv("KATALOGIN_ADMIN_TOKEN", raising=False)
    klien_tanpa_token = TestClient(
        create_app(db_path=str(tmp_path / "tanpa-token.db"), admin_token=None)
    )

    respons = klien_tanpa_token.post(
        "/admin/kredit",
        headers={"X-Admin-Token": "token-uji"},
        json={"user_id": "andi", "jumlah": 10},
    )

    assert respons.status_code == 403
    assert respons.json() == {"detail": "Token admin tidak valid"}


def test_admin_kredit_menolak_jumlah_di_luar_rentang(klien) -> None:
    respons_nol = klien.post(
        "/admin/kredit",
        headers={"X-Admin-Token": "token-uji"},
        json={"user_id": "andi", "jumlah": 0},
    )
    respons_terlalu_besar = klien.post(
        "/admin/kredit",
        headers={"X-Admin-Token": "token-uji"},
        json={"user_id": "andi", "jumlah": 100001},
    )

    assert respons_nol.status_code == 422
    assert respons_terlalu_besar.status_code == 422


def test_admin_kredit_menolak_user_id_tidak_valid(klien) -> None:
    respons = klien.post(
        "/admin/kredit",
        headers={"X-Admin-Token": "token-uji"},
        json={"user_id": "a b", "jumlah": 10},
    )

    assert respons.status_code == 400
    assert respons.json() == {"detail": "user_id tidak valid"}
