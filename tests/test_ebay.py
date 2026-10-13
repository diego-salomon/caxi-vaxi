import copy
import json
import sys
import types
from datetime import datetime, timedelta, timezone

import ebay
from conftest import FICHA_EBAY, RESUMEN_EBAY


def test_filtro_espana_y_ue():
    assert ebay.filtro(900) == "price:[..900],priceCurrency:EUR,itemLocationCountry:ES"
    assert ebay.filtro(600, ue=True).endswith("itemLocationRegion:EUROPEAN_UNION")


def test_normalizar_con_ficha():
    l = ebay.normalizar(RESUMEN_EBAY, FICHA_EBAY, "2026-10-13T10:00:00+00:00")
    assert l["casa"] == "ebay" and l["precio_fijo"] is True
    assert l["salida"] == 350.0
    assert l["url"] == "https://www.ebay.es/itm/1234567890"
    # medidas de los aspectos, con unidades mezcladas
    assert l["lado_mayor_cm"] == 160
    assert "160 x 45 x 75 cm" in l["texto"]
    assert "Material: Teca" in l["texto"] and "Marca" not in l["texto"]
    assert l["imagen"].endswith("/s-l500.jpg")
    assert l["imagen_grande"].endswith("/s-l1600.jpg")
    # la rebaja la marca el propio anuncio
    assert l["precio_anterior"] == 420.0
    assert l["obtenido"] == "2026-10-13T10:00:00+00:00"


def test_no_guarda_nada_del_vendedor():
    """Licencia: nada de User IDs. Y es lo que se declara en la exencion."""
    l = ebay.normalizar(RESUMEN_EBAY, FICHA_EBAY)
    plano = json.dumps(l, ensure_ascii=False)
    assert "alguien_real" not in plano
    assert "feedback" not in plano and "seller" not in plano


def test_subasta():
    s = copy.deepcopy(RESUMEN_EBAY)
    s["buyingOptions"] = ["AUCTION"]
    s["currentBidPrice"] = {"value": "40.00", "currency": "EUR"}
    s["itemEndDate"] = "2026-10-15T18:30:00.000Z"
    l = ebay.normalizar(s)
    assert l["salida"] == 40.0 and l["precio_fijo"] is False
    assert any("SUBASTA" in a and "2026-10-15 18:30" in a for a in l["avisos_fuente"])


def test_fuera_de_espana_y_otra_moneda():
    s = copy.deepcopy(RESUMEN_EBAY)
    s["itemLocation"] = {"country": "IT"}
    s["price"] = {"value": "100.00", "currency": "GBP"}
    l = ebay.normalizar(s)
    assert l["salida"] == 117.0 and l["ubicacion"] == "IT"
    assert len(l["avisos_fuente"]) == 2


def test_sin_precio_no_entra():
    s = copy.deepcopy(RESUMEN_EBAY)
    del s["price"]
    assert ebay.normalizar(s) is None


def test_medidas_de_la_descripcion_si_no_hay_aspectos():
    s = copy.deepcopy(RESUMEN_EBAY)
    s["title"] = "Cómoda vintage 120 cm de ancho, 80 cm de alto"
    assert ebay.normalizar(s)["lado_mayor_cm"] == 120


def test_credenciales(monkeypatch):
    monkeypatch.setitem(sys.modules, "config_local", types.SimpleNamespace())
    cred, error = ebay.credenciales()
    assert cred is None and "EBAY_CLIENT_ID" in error
    monkeypatch.setitem(sys.modules, "config_local",
                        types.SimpleNamespace(EBAY_CLIENT_ID="id", EBAY_CLIENT_SECRET="sec"))
    assert ebay.credenciales() == (("id", "sec"), None)


class _Resp:
    status_code = 200

    def json(self):
        return {"access_token": "tok-1", "expires_in": 7200}


def test_token_se_reutiliza_hasta_que_caduca(tmp_path, monkeypatch):
    monkeypatch.setattr(ebay, "CACHE_TOKEN", str(tmp_path / "ebay_token.json"))
    monkeypatch.setattr(ebay, "DIR_DATOS", str(tmp_path))
    llamadas = []

    def post(url, **kw):
        llamadas.append(kw)
        return _Resp()
    monkeypatch.setattr(ebay.requests, "post", post)
    assert ebay.token(("id", "secreto"), ahora=1000) == "tok-1"
    assert ebay.token(("id", "secreto"), ahora=1000 + 3600) == "tok-1"
    assert len(llamadas) == 1
    assert llamadas[0]["data"]["scope"] == "https://api.ebay.com/oauth/api_scope"
    assert llamadas[0]["headers"]["Authorization"].startswith("Basic ")
    # a menos de 5 minutos de caducar se pide otro
    ebay.token(("id", "secreto"), ahora=1000 + 7200 - 200)
    assert len(llamadas) == 2
    # el secreto no se escribe en datos/
    assert "secreto" not in (tmp_path / "ebay_token.json").read_text()


def _archivo(tmp_path, monkeypatch, horas):
    ruta = tmp_path / "ebay.json"
    monkeypatch.setattr(ebay, "ARCHIVO", str(ruta))
    t = (datetime.now(timezone.utc) - timedelta(hours=horas)).isoformat(timespec="seconds")
    ruta.write_text(json.dumps({"obtenido": t, "lotes": [{"url": "u"}]}))


def test_caduca_a_las_seis_horas(tmp_path, monkeypatch):
    _archivo(tmp_path, monkeypatch, 5)
    assert ebay.cargar_si_fresco()[0] == [{"url": "u"}]
    _archivo(tmp_path, monkeypatch, 7)
    lotes, estado = ebay.cargar_si_fresco()
    assert lotes == [] and "caducados" in estado


def test_rastrear_sin_claves_no_llama(monkeypatch):
    monkeypatch.setitem(sys.modules, "config_local", types.SimpleNamespace())
    monkeypatch.setattr(ebay.requests, "post", lambda *a, **k: (_ for _ in ()).throw(AssertionError))
    assert ebay.rastrear() == []


def test_rastrear_pide_fichas_de_20_en_20(monkeypatch):
    monkeypatch.setitem(sys.modules, "config_local",
                        types.SimpleNamespace(EBAY_CLIENT_ID="id", EBAY_CLIENT_SECRET="s"))
    monkeypatch.setattr(ebay, "token", lambda cred: "tok")
    monkeypatch.setattr(ebay, "PAUSA", 0)
    pedidas = []

    def get(self, ruta, **params):
        pedidas.append((ruta, params))
        self.n += 1
        if ruta.endswith("/search"):
            base = len(pedidas) * 1000
            out = []
            for i in range(25):
                s = copy.deepcopy(RESUMEN_EBAY)
                s["itemId"] = f"v1|{base + i}|0"
                out.append(s)
            return {"itemSummaries": out}
        return {"items": [dict(FICHA_EBAY, itemId=i) for i in params["item_ids"].split(",")]}
    monkeypatch.setattr(ebay.Ebay, "get", get)
    lotes = ebay.rastrear(["aparador", "comoda"])
    assert len(lotes) == 50
    busquedas = [p for r, p in pedidas if r.endswith("/search")]
    assert busquedas[0]["filter"].endswith("itemLocationCountry:ES")
    fichas = [p for r, p in pedidas if r.endswith("/item/")]
    assert [len(p["item_ids"].split(",")) for p in fichas] == [20, 20, 10]
    assert all(l["lado_mayor_cm"] == 160 for l in lotes)
