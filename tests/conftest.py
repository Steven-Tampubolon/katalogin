import pytest

from katalogin.models import Product


@pytest.fixture
def kaos() -> Product:
    return Product(
        nama="Kaos Polos Pria",
        merek="Oneck",
        bahan="Katun Combed 30s",
        ukuran="L",
        warna="Hitam",
        fungsi="Harian",
        fitur=["Adem", "Tidak Mudah Luntur"],
    )
