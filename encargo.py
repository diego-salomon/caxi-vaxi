# -*- coding: utf-8 -*-
"""
ENCARGO: una busqueda con restricciones duras, no solo de gusto.

La diferencia con el ranking normal: aqui hay medidas que NO se negocian.
Un mueble que no cabe no es una oportunidad, es un problema de logistica.

Uso:
    from encargo import CAJONERA_DORMITORIO, buscar
    buscar(CAJONERA_DORMITORIO)
"""
import json
import warnings
warnings.simplefilter('ignore')
import os
import re

from puntuar import limpiar, puntuar
from scraper import DIR_DATOS

# ---------------------------------------------------------------------------
# Extraccion de TODAS las dimensiones, no solo la mayor
# ---------------------------------------------------------------------------
RE_DIM = re.compile(
    r"(\d{1,4}(?:[.,]\d+)?)\s*(?:x|X|×|por)\s*"
    r"(\d{1,4}(?:[.,]\d+)?)"
    r"(?:\s*(?:x|X|×|por)\s*(\d{1,4}(?:[.,]\d+)?))?"
    r"\s*(cm|mm|m\b|metros?)?", re.I)


def _f(x):
    try:
        return float(str(x).replace(",", "."))
    except (TypeError, ValueError):
        return None


def dimensiones(texto):
    """Devuelve lista de tuplas de dimensiones en cm, ordenadas de mayor a menor."""
    salida = []
    for m in RE_DIM.finditer(texto or ""):
        unidad = (m.group(4) or "cm").lower()
        factor = {"mm": 0.1, "m": 100.0, "metro": 100.0, "metros": 100.0}.get(unidad, 1.0)
        vals = [_f(g) for g in (m.group(1), m.group(2), m.group(3)) if g]
        vals = [v * factor for v in vals if v is not None]
        vals = [v for v in vals if 2 < v < 500]
        if len(vals) >= 2:
            salida.append(tuple(sorted(vals, reverse=True)))
    return salida


def cabe(texto, limites):
    """
    limites: dict con max_cm por eje, p.ej. {"mayor": 220, "segundo": 200, "menor": 70}
    Devuelve (cabe, dims_encontradas, motivo).
    Si no hay medidas en el texto, NO descarta: devuelve None para que lo revises tu.
    """
    dims = dimensiones(texto)
    if not dims:
        return None, [], "sin medidas en el catalogo"
    for d in dims:
        mayor = d[0]
        segundo = d[1] if len(d) > 1 else 0
        menor = d[2] if len(d) > 2 else 0
        if limites.get("mayor") and mayor > limites["mayor"]:
            continue
        if limites.get("segundo") and segundo > limites["segundo"]:
            continue
        if limites.get("menor") and menor and menor > limites["menor"]:
            continue
        if limites.get("min_mayor") and mayor < limites["min_mayor"]:
            continue
        return True, dims, f"{' x '.join(f'{v:.0f}' for v in d)} cm"
    return False, dims, f"no cabe: {dims[0]}"


# ---------------------------------------------------------------------------
# ENCARGOS
# ---------------------------------------------------------------------------
CAJONERA_DORMITORIO = {
    "nombre": "Cajonera / aparador para el dormitorio",
    "notas": (
        "Referencia: los armarios de dormitorio de Luis Barragan, a la altura de la puerta, "
        "sin lineas, muy sencillos. La puerta de Diego mide 200 cm, asi que la pieza tiene "
        "que PASAR por ella. Su referencia concreta es el armario de Ico Parisi para "
        "Fratelli Reguitti: almacenaje italiano mid-century, no 'una comoda'. "
        "Las comodas genericas las descarta explicitamente."
    ),
    # El ancho es el limite que no se negocia.
    "limites": {"mayor": 220, "segundo": 200, "menor": 70},
    "ideal": "190-220 cm de ancho, hasta 200 de alto, unos 60 de fondo",
    "alternativa": {"limites": {"mayor": 130, "min_mayor": 90, "menor": 70},
                    "desc": "aparador o cajonera de 90-130 cm, altura media"},
    "precio_max": 600,
    # OJO: "buffet" y "bufet" estaban aqui y colaban cuadros de Bernard Buffet.
    # Los apellidos de artista chocan con los nombres de mueble. Fuera.
    "tipos": ["cajonera", "comoda", "aparador", "sideboard", "credenza",
              "armario", "mueble bajo", "chest of drawers", "dresser",
              "mueble auxiliar", "consola", "cajonero", "chiffonier"],
    "excluir": ["castellan", "isabelin", "barroc", "luis xv", "luis xvi", "renacimiento",
                "bargueno", "religios", "vitrina ingles", "luis felipe", "luis philippe",
                "ikea", "malm", "koppang", "maisons du monde", "tallada", "tallado",
                "marqueteria", "dorada", "estucad"],
}


def buscar(enc, lotes=None, incluir_alternativa=True):
    if lotes is None:
        ruta = os.path.join(DIR_DATOS, "lotes.json")
        lotes = json.load(open(ruta, encoding="utf-8")) if os.path.exists(ruta) else []

    resultados = []
    for raw in lotes:
        l = puntuar(dict(raw))
        titulo = limpiar(l.get("titulo", ""))
        txt = limpiar(l.get("titulo", "") + " " + l.get("texto", ""))

        # El TIPO de mueble tiene que estar en el TITULO. Buscarlo en todo el
        # cuerpo colaba tapices y percheros porque la ficha mencionaba "mesa"
        # de pasada.
        # Segre suelta los <br> pegados en sus slugs ("biokbrcomoda"), asi que
        # el titulo no basta. Se mira tambien el arranque del texto, que si
        # viene limpio, pero NO el cuerpo entero (eso colaba percheros).
        cabecera = titulo + " . " + limpiar(l.get("texto", "")[:160])
        if not any(re.search(r"(?<![a-z])" + re.escape(limpiar(t)) + r"(?![a-z])", cabecera)
                   for t in enc["tipos"]):
            continue
        if any(limpiar(x) in txt for x in enc.get("excluir", [])):
            continue
        # Puntuacion negativa = choca con su gusto. Fuera, por mucho que quepa.
        if l["puntos"] < 0:
            continue
        salida = l.get("salida") or 0
        if salida and salida > enc["precio_max"]:
            continue

        ok, dims, motivo = cabe(l.get("texto", ""), enc["limites"])
        via = "principal"
        if ok is False and incluir_alternativa and enc.get("alternativa"):
            ok2, dims2, motivo2 = cabe(l.get("texto", ""), enc["alternativa"]["limites"])
            if ok2:
                ok, _, motivo, via = True, dims2, motivo2, "alternativa"
        if ok is False:
            continue

        l["encaje"] = motivo
        l["via"] = via if ok else "sin medidas"
        resultados.append(l)

    orden = {"principal": 0, "alternativa": 1, "sin medidas": 2}
    return sorted(resultados, key=lambda x: (orden[x["via"]], -x["puntos"], x.get("salida") or 0))


def informe(enc, res):
    out = [f"\n{'=' * 78}", f"  ENCARGO: {enc['nombre']}", f"  {enc['notas']}",
           f"  Medida ideal: {enc['ideal']}   ·   Tope: {enc['precio_max']} EUR",
           f"{'=' * 78}", f"\n  {len(res)} candidatos\n"]
    for l in res:
        marca = {"principal": "ENCAJA", "alternativa": "alternativa",
                 "sin medidas": "SIN MEDIDAS, hay que preguntar"}[l["via"]]
        c = l.get("coste", {})
        out.append(f"[{l['puntos']:+3d}] {marca:28s} {l['casa_nombre']} lote {l.get('lote') or '?'}")
        out.append(f"      {l['titulo'][:92]}")
        out.append(f"      {l['encaje']}")
        if c:
            out.append(f"      salida {c['martillo']:.0f} EUR -> TOTAL {c['total']:.0f} EUR")
        if l.get("no_vendido"):
            out.append("      NO VENDIDO: negociable o va a bajar")
        for b in l["banderas"][:2]:
            out.append(f"      OJO: {b}")
        out.append(f"      {l['url']}")
        out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    enc = CAJONERA_DORMITORIO
    res = buscar(enc)
    print(informe(enc, res))
