import copy

import ebay
import puntuar
import wallapop
from conftest import FICHA, FICHA_EBAY, RESUMEN_EBAY
from vista import preparar


def test_ebay_va_aparte_con_su_hora():
    l = ebay.normalizar(RESUMEN_EBAY, FICHA_EBAY, "2026-10-13T10:00:00+00:00")
    d = preparar([puntuar.puntuar(dict(l))])[0]
    assert d["aparte"] is True and d["grupo"] == "eBay"
    assert d["obt"] == "2026-10-13T10:00:00+00:00"


def test_wallapop_se_mezcla_y_lleva_sello_de_reservado():
    f = copy.deepcopy(FICHA)
    f["flags"]["reserved"] = True
    l = wallapop.registro(f, "articulo")
    d = preparar([puntuar.puntuar(dict(l))])[0]
    assert d["aparte"] is False and d["obt"] is None
    assert d["res"] is True and d["grupo"] == "Wallapop"


def test_rebaja_de_wallapop_sube_la_oportunidad():
    l = wallapop.registro(FICHA, "articulo")
    sin = preparar([puntuar.puntuar(dict(l))])[0]["o"]
    l["precio_anterior"] = 600.0
    con = preparar([puntuar.puntuar(dict(l))])[0]["o"]
    assert con > sin


def test_ebay_sigue_vigente_aunque_visto_sea_viejo():
    l = ebay.normalizar(RESUMEN_EBAY)
    l["visto"] = "2026-01-01T00:00:00+00:00"
    assert puntuar.vigente(l)
