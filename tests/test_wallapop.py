import copy
import sys
import types

import pytest

import wallapop as w
from conftest import FICHA, PORTADA_PAGINA, VENDEDOR_PAGINA, pagina
from scraper import ParadaTotal


def test_lee_next_data():
    assert w.datos_pagina(pagina({"item": FICHA}))["item"]["slug"] == FICHA["slug"]
    assert w.datos_pagina("<html>sin datos</html>") is None
    assert w.datos_pagina(None) is None


def test_ficha():
    l = w.registro(FICHA, "articulo", "vendedor-1")
    assert l["casa"] == "wallapop" and l["precio_fijo"] is True
    assert l["salida"] == 450.0
    assert l["url"] == "https://es.wallapop.com/item/aparador-danes-de-teca-1000000001"
    assert l["lote"] == "1000000001"
    # el numero va delante del eje: "190cm ancho x 42cm fondo x 78cm alto"
    assert l["lado_mayor_cm"] == 190
    assert "190 x 42 x 78 cm" in l["texto"]
    # el parrafo de etiquetas para buscadores no entra en el texto que se puntua
    assert "Danish" not in l["texto"] and "Space age" not in l["texto"]
    assert l["imagen"].endswith("pictureSize=W640")
    assert l["imagen_grande"].endswith("pictureSize=W800")
    assert l["ubicacion"] == "Madrid" and l["vendedor"] == "vendedor-1"
    assert not l["reservado"] and not l["vendido"]


def test_flags_de_la_ficha():
    f = copy.deepcopy(FICHA)
    f["flags"]["onHold"] = True
    assert w.registro(f, "articulo")["reservado"]
    f["flags"]["sold"] = True
    assert w.registro(f, "articulo")["vendido"]


def test_measures_relleno_manda():
    f = copy.deepcopy(FICHA)
    f["measures"] = {"width_cm": 120, "height_cm": 80, "length_cm": 40}
    assert w.registro(f, "articulo")["lado_mayor_cm"] == 120


def test_perfil_y_portada():
    perfil = [w.registro(a, "vendedor", "vendedor-1", "Alcalá de Henares")
              for a in VENDEDOR_PAGINA["publishedItems"]["data"]]
    assert perfil[0]["reservado"] and perfil[0]["salida"] == 80.0
    assert perfil[0]["ubicacion"] == "Alcalá de Henares"
    assert perfil[0]["lado_mayor_cm"] == 85
    portada = w.registro(PORTADA_PAGINA["seoLandingData"]["items"][0], "portada")
    assert portada["salida"] == 120.0 and portada["vendedor"] == "otro-vendedor-9"
    assert portada["imagen"].endswith("W640")


@pytest.mark.parametrize("desc,queda,fuera", [
    ("Mesa de cristal. En buen estado. tags: butaca sofa aparador togo kartell",
     "En buen estado.", "kartell"),
    ("Sillas Bauhaus en terciopelo. Precio del set 200eur. silla vintage, mid century, "
     "cantilever, cesca, breuer, stam, lc1, mobles 114 pilma mesa centro bufet, Wassily",
     "Precio del set 200eur.", "breuer"),
    ("Mesa de roble, nogal y haya, con patas de hierro.",
     "Mesa de roble, nogal y haya", None),
])
def test_sin_etiquetas(desc, queda, fuera):
    limpio = w.sin_etiquetas(desc)
    assert queda in limpio
    if fuera:
        assert fuera not in limpio


@pytest.mark.parametrize("texto,esperado", [
    ("Medidas: 190cm ancho x 42cm fondo x 78cm alto", {"ancho": 190, "fondo": 42, "alto": 78}),
    ("1,10 m de alto por 84 cm de ancho", {"alto": 110, "ancho": 84}),
    ("sin medidas", {}),
])
def test_medidas_num_eje(texto, esperado):
    assert w.medidas_num_eje(texto) == esperado


def _prev(l, **cambios):
    p = dict(l)
    p.update(cambios)
    return {p["url"]: p}


def test_bajada_de_precio():
    l = w.registro(FICHA, "articulo")
    cambios = w.comparar([l], _prev(l, salida=600.0), set())
    assert l["precio_anterior"] == 600.0
    assert [c[0] for c in cambios] == ["baja"]


def test_rebaja_se_mantiene_mientras_no_cambie():
    l = w.registro(FICHA, "articulo")
    cambios = w.comparar([l], _prev(l, precio_anterior=600.0), set())
    assert l["precio_anterior"] == 600.0 and cambios == []


def test_pasa_a_reservado():
    f = copy.deepcopy(FICHA)
    f["flags"]["reserved"] = True
    l = w.registro(f, "articulo")
    cambios = w.comparar([l], _prev(l, reservado=False), set())
    assert [c[0] for c in cambios] == ["reservado"]
    assert "RESERVADO en Wallapop" in l["avisos_fuente"]


def test_nuevo_de_vendedor_vigilado():
    viejo, nuevo = [w.registro(a, "vendedor", "vendedor-1")
                    for a in VENDEDOR_PAGINA["publishedItems"]["data"]]
    previos = {viejo["url"]: dict(viejo)}
    cambios = w.comparar([dict(viejo), nuevo], previos, {"vendedor-1"})
    assert [c[0] for c in cambios] == ["nuevo"]
    assert nuevo["nuevo_de_vendedor"]


def test_vendedor_mirado_por_primera_vez_no_da_nuevos():
    lotes = [w.registro(a, "vendedor", "vendedor-1") for a in VENDEDOR_PAGINA["publishedItems"]["data"]]
    assert w.comparar(lotes, {}, {"vendedor-1"}) == []


def test_desaparecidos():
    l = w.registro(FICHA, "articulo")
    perdidos = w.desaparecidos([FICHA["slug"]], {l["url"]: l})
    assert perdidos == [l]
    assert w.desaparecidos([FICHA["slug"]], {}) == []


def test_listas_acepta_urls_pegadas(monkeypatch):
    falso = types.SimpleNamespace(
        WALLAPOP_ARTICULOS=["https://es.wallapop.com/item/comoda-1000000009?utm=x", "mal slug!"],
        WALLAPOP_VENDEDORES=["https://es.wallapop.com/user/vendedor-1/"],
        WALLAPOP_PORTADAS=["muebles-deco-y-jardin/aparador-vintage/madrid", "search?keywords=x"])
    monkeypatch.setitem(sys.modules, "config_local", falso)
    art, vend, port = w.listas()
    assert art == ["comoda-1000000009"]
    assert vend == ["vendedor-1"]
    assert port == ["muebles-deco-y-jardin/aparador-vintage/madrid"]


def test_portadas_por_defecto_mas_descubiertas(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "config_local", types.SimpleNamespace())
    monkeypatch.setattr(w, "DESCUBIERTAS", str(tmp_path / "no-existe.json"))
    assert w.listas()[2] == w.PORTADAS
    extra = tmp_path / "descubiertas.json"
    extra.write_text('["muebles-deco-y-jardin/aparador-teca/madrid"]')
    monkeypatch.setattr(w, "DESCUBIERTAS", str(extra))
    assert w.listas()[2] == w.PORTADAS + ["muebles-deco-y-jardin/aparador-teca/madrid"]


def test_sugeridas_y_candidatas():
    seo = {"header": {"suggestedKeywords": [{"url": "/muebles-deco-y-jardin/aparador-antiguo"},
                                            {"url": "/muebles-deco-y-jardin/aparador-ikea"}]},
           "footer": {"suggestedKeywords": [{"url": "/muebles-deco-y-jardin/aparador-retro/madrid"},
                                            {"url": "/search?keywords=x"}]}}
    sug = w.sugeridas_de(seo)
    assert sug == {"muebles-deco-y-jardin/aparador-antiguo/madrid",
                   "muebles-deco-y-jardin/aparador-ikea/madrid",
                   "muebles-deco-y-jardin/aparador-retro/madrid"}
    # ikea fuera por gusto; aparador-retro ya se lee
    assert w.candidatas(sug, set(w.PORTADAS)) == ["muebles-deco-y-jardin/aparador-antiguo/madrid"]


def _web_falsa(monkeypatch, pedidas):
    def traer(url):
        pedidas.append(url)
        if "/item/" in url:
            return None if url.endswith("borrado-1000000099") else pagina({"item": FICHA})
        if "/user/" in url:
            return pagina(VENDEDOR_PAGINA)
        return pagina(PORTADA_PAGINA)
    monkeypatch.setattr(w, "traer", traer)


def test_pasada_con_tope_y_sin_buscador(monkeypatch):
    falso = types.SimpleNamespace(
        WALLAPOP_ARTICULOS=[FICHA["slug"], "borrado-1000000099"],
        WALLAPOP_VENDEDORES=["vendedor-1"],
        WALLAPOP_PORTADAS=[f"muebles-deco-y-jardin/tema-{i}/madrid" for i in range(100)])
    monkeypatch.setitem(sys.modules, "config_local", falso)
    pedidas = []
    _web_falsa(monkeypatch, pedidas)
    lotes, sin_ficha, vendedores = w.rastrear()
    assert len(pedidas) == w.TOPE_PAGINAS
    assert not any("/search" in u or "?" in u for u in pedidas)
    assert sin_ficha == ["borrado-1000000099"]
    precios = sorted(l["salida"] for l in lotes)
    # la lampara de 2.500 EUR del perfil y el regalo a 0 EUR de la portada se quedan fuera
    assert precios == [80.0, 120.0, 450.0]


def test_un_403_para_todo(monkeypatch):
    monkeypatch.setitem(sys.modules, "config_local", types.SimpleNamespace(
        WALLAPOP_ARTICULOS=[FICHA["slug"]], WALLAPOP_VENDEDORES=[], WALLAPOP_PORTADAS=[]))

    def traer(url):
        raise ParadaTotal("403")
    monkeypatch.setattr(w, "traer", traer)
    with pytest.raises(ParadaTotal):
        w.rastrear()


def test_guardar_sobrescribe_y_cargar_quita_vendidos(tmp_path, monkeypatch):
    monkeypatch.setattr(w, "ARCHIVO", str(tmp_path / "wallapop.json"))
    monkeypatch.setattr(w, "DIR_DATOS", str(tmp_path))
    vivo = w.registro(FICHA, "articulo")
    f = copy.deepcopy(FICHA)
    f["slug"] = "otro-1000000010"
    f["flags"]["sold"] = True
    vendido = w.registro(f, "articulo")
    w.guardar([vivo, vendido], [], [])
    w.guardar([vivo, vendido], [], [])
    lotes, estado = w.cargar()
    assert [l["url"] for l in lotes] == [vivo["url"]]
    assert estado.startswith("Wallapop de hace")
