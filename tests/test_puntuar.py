"""
Tests de la puntuacion y del coste por casa.

Cubren los falsos positivos de vocabulario que se vieron auditando (y que los
comentarios del codigo documentan) y los tramos de comision. Sin red.
"""
import casas
import puntuar
from puntuar import _encaja


def p(titulo="", texto="", casa="salaretiro", salida=100):
    """Puntua un lote minimo y devuelve el dict resultado."""
    return puntuar.puntuar({"titulo": titulo, "texto": texto, "casa": casa,
                            "salida": salida, "url": "x"})


def banderas(**kw):
    return p(**kw)["banderas"]


# --- palabras completas que saltaban dentro de otra palabra ---

def test_posterior_no_es_poster():
    assert not any("poster" in b for b in banderas(texto="mueble con la tapa posterior de madera"))


def test_laminado_no_es_lamina():
    assert not any("NO: lamina" in b for b in banderas(texto="tablero laminado en roble"))


def test_estampado_no_es_estampa():
    assert not any("NO: estampa" in b for b in banderas(texto="tela con estampado floral"))


def test_poster_penaliza_pero_posterior_no():
    neutro = p(texto="mesa de madera")["puntos"]
    assert p(texto="mesa de madera con tapa posterior")["puntos"] == neutro   # no penaliza
    assert p(texto="mesa de madera y un poster")["puntos"] < neutro            # si penaliza


# --- "castellan" saltaba en el Paseo de la Castellana ---

def test_castellana_calle_no_descarta():
    assert p(texto="recogida en Paseo de la Castellana, Madrid")["rechazado"] is False


def test_mueble_castellano_si_descarta():
    assert p(titulo="Mueble castellano de nogal")["rechazado"] is True


# --- otros falsos positivos ya documentados en el codigo ---

def test_subarroca_no_es_barroco():
    assert p(titulo="Obra firmada por Subarroca")["rechazado"] is False


# --- "segun"/"estilo" solo cuentan en el titulo, no en la descripcion ---

def test_segun_en_descripcion_no_marca_atribucion():
    assert not any("segun" in b for b in banderas(texto="segun la tradicion popular venezolana"))


def test_segun_en_titulo_si_marca_atribucion():
    assert any("segun" in b for b in banderas(titulo="Bodegon segun Zurbaran"))


# --- disenadores que estaban atrapados dentro de un comentario ---

def test_joe_colombo_ahora_puntua():
    sin = p(titulo="Silla")["puntos"]
    assert p(titulo="Silla de Joe Colombo")["puntos"] == sin + 3   # peso del disenador


def test_kazuhide_takahama_ahora_puntua():
    sin = p(titulo="Lampara")["puntos"]
    assert p(titulo="Lampara de Kazuhide Takahama")["puntos"] == sin + 3


# --- _encaja: limite de palabra para las claves de palabra completa ---

def test_encaja_fin_palabra():
    assert _encaja("poster", "poster antiguo", estricto=True)
    assert _encaja("poster", "tres posters", estricto=True)       # plural, si
    assert not _encaja("poster", "cara posterior", estricto=True)  # dentro de otra, no


# --- coste real por casa ---

def test_ansorena_25_por_ciento_hasta_1000():
    _, d = casas.coste_total(900, "ansorena")
    assert round(d["comision"], 2) == 225.0        # 900 * 0.25


def test_ansorena_23_por_ciento_por_encima_de_1000():
    _, d = casas.coste_total(1500, "ansorena")
    assert round(d["comision"], 2) == 345.0        # 1500 * 0.23


def test_segre_lleva_iva_sobre_la_comision():
    _, d = casas.coste_total(1000, "segre")
    assert round(d["comision"], 2) == 217.8        # 1000 * 0.18 * 1.21


def test_tienda_sin_comision():
    _, d = casas.coste_total(500, "pamono")        # no esta en CASAS: precio final
    assert d["comision"] == 0.0 and d["total"] == 500
