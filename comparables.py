# -*- coding: utf-8 -*-
"""
COMPARABLES: contesta "¿esto esta barato?" en vez de solo "¿esto me gusta?".

Fuente: datos/historico.json, el archivo publicado por la propia Alcala
(27.051 lotes, 13.018 marcados VENDIDO, con precio de remate en el texto).

QUE CAMBIO RESPECTO A LA PRIMERA VERSION, Y POR QUE HACIA FALTA
---------------------------------------------------------------
La v1 emparejaba por vocabulario suelto y daba veredictos sin sentido: comparaba
un aparador de los 60 contra un escritorio Carlos III porque los dos decian
"nogal", y una comoda de Basterretxea contra un lote de gemelos de bisuteria.

Ahora:
  1. Se exige MISMA CATEGORIA (mueble, pintura, escultura, lampara, alfombra,
     ceramica, plata, libro). Nada cruza categorias.
  2. Se exige EPOCA COMPATIBLE. Un mueble del XVIII no sirve de comparable
     para uno de los 60, por mucha palabra que compartan.
  3. Se usa el PRECIO DE REMATE cuando existe, no el de salida. Son cosas
     distintas: la salida es lo que pedian, el remate es lo que pagaron.
  4. Si no hay al menos 6 comparables validos, NO se da veredicto. Antes
     inventaba una mediana con cuatro trastos y sonaba a dato.
"""
import json
import warnings
warnings.simplefilter('ignore')
import os
import re
import statistics
import unicodedata

from scraper import DIR_DATOS

# --------------------------------------------------------------------------
CATEGORIAS = [
    ("mueble", r"\b(mueble|comoda|aparador|armario|mesa|mesita|silla|sillon|butaca|"
               r"consola|vitrina|estanteria|libreria|escritorio|buro|canape|sofa|"
               r"banco|taburete|velador|arcon|bargueno|camas?|cabecero|chifonier)\b"),
    ("lampara", r"\b(lampara|aplique|candelabro|candelero|arana|farol|quinque|flexo|"
                r"plafon|luminaria)\b"),
    ("pintura", r"\b(oleo|acuarela|gouache|temple|pintura|lienzo|tabla|cuadro|"
                r"bodegon|paisaje|retrato|marina)\b"),
    ("obra_grafica", r"\b(grabado|litografia|serigrafia|aguafuerte|estampa|xilografia|"
                     r"punta seca|cartel)\b"),
    ("escultura", r"\b(escultura|busto|talla|figura|bronce|terracota|relieve|"
                  r"estatua|estatuilla)\b"),
    ("alfombra", r"\b(alfombra|tapiz|kilim|moqueta)\b"),
    ("ceramica", r"\b(ceramica|porcelana|loza|faience|gres|vidriado|azulejo|jarron|"
                 r"plato|vajilla|fuente de)\b"),
    ("plata", r"\b(plata|platero|punzon|cuberteria|bandeja de plata|orfebreria)\b"),
    ("libro", r"\b(libro|manuscrito|incunable|encuadernad|volumen|tomo)\b"),
    ("reloj", r"\b(reloj|cronometro|pendulo)\b"),
]

EPOCAS = [
    ("antiguo",  r"s\.?\s*(x?vi{1,3}|xi{0,3}v?|xvii|xviii)\b|siglo\s*xv?i{1,3}\b|"
                 r"\b1[4-7]\d{2}\b|gotic|renacimient|barroc|carlos i{1,3}v?\b|felipe v"),
    ("xix",      r"s\.?\s*xix\b|siglo\s*xix|\b18\d{2}\b|isabelin|fernandin|imperio|"
                 r"napoleon iii|victorian|alfonsin"),
    ("principios", r"\b19[0-3]\d\b|art nouveau|art deco|modernist|jugendstil"),
    ("medio",    r"\b19[4-7]\d\b|a[nñ]os (4|5|6|7)0\b|mid.?century|mid.?siglo|space age"),
    ("reciente", r"\b19[89]\d\b|\b20[0-2]\d\b|a[nñ]os (8|9)0\b|contemporane|posmoderno"),
]

# epocas que pueden compararse entre si
VECINAS = {
    "antiguo": {"antiguo", "xix"},
    "xix": {"xix", "antiguo", "principios"},
    "principios": {"principios", "xix", "medio"},
    "medio": {"medio", "principios", "reciente"},
    "reciente": {"reciente", "medio"},
    None: set(),
}

VACIAS = set("""de la el los las un una unos unas y o en con para por sobre su sus del al
cm mm aprox approx medidas medida decorado decorada decorados con como que mas muy dos tres
cuatro sin segun estilo epoca siglo lote pareja juego conjunto color colores forma sobre
base parte alto ancho largo diametro altura anchura peso gr kg firmado firmada fechado
vendido buen estado falta faltas restaurado""".split())

RE_REMATE = re.compile(r"(remat\w*|adjudic\w*|precio final|vendido por)\D{0,14}([\d.]+)(?:,\d+)?\s*€", re.I)


def norm(s):
    s = (s or "").lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]", " ", s)


def categoria(texto):
    t = norm(texto)
    for nombre, rx in CATEGORIAS:
        if re.search(rx, t):
            return nombre
    return None


RE_RUIDO = re.compile(r"\b(lote|lot|ref|referencia|n[uo]m)\s*\.?\s*\d+", re.I)
RE_INICIO_NUM = re.compile(r"^\s*\d{1,5}\s*[.\-]")


def epoca(texto):
    """
    Devuelve la epoca, o None si no esta clara.

    Dos trampas que costaron un rato:
      - El NUMERO DE LOTE se leia como año: "lote 1386" encajaba con el patron
        de 1400-1700 y mandaba un mueble de los 60 al siglo XVIII.
      - Las FECHAS DEL AUTOR tampoco son la fecha del objeto: "Basterretxea
        1924-2014" no dice cuando se hizo la comoda.
    Por eso se limpia el ruido primero y luego se cuenta: gana la epoca con mas
    señales, y si hay empate se devuelve None. Preferimos no saber a inventar.
    """
    t = norm(texto)
    t = RE_INICIO_NUM.sub(" ", t)
    t = RE_RUIDO.sub(" ", t)
    puntos = {}
    for nombre, rx in EPOCAS:
        n = len(re.findall(rx, t))
        if n:
            puntos[nombre] = n
    if not puntos:
        return None
    orden = sorted(puntos.items(), key=lambda x: -x[1])
    if len(orden) > 1 and orden[0][1] == orden[1][1]:
        return None
    return orden[0][0]


def clave(l):
    t = (l.get("titulo") or "") + " " + (l.get("texto") or "")[:400]
    return categoria(t), epoca(t)


def palabras(texto):
    return {w for w in norm(texto).split() if len(w) > 3 and w not in VACIAS}


def remate(l):
    """Precio pagado de verdad, si el archivo lo trae. Si no, None."""
    m = RE_REMATE.search(l.get("texto") or "")
    if not m:
        return None
    try:
        v = float(m.group(2).replace(".", ""))
    except ValueError:
        return None
    return v if v > 0 else None


# --------------------------------------------------------------------------
_CACHE = {}


def _indice():
    if "idx" in _CACHE:
        return _CACHE["idx"], _CACHE["hist"]
    ruta = os.path.join(DIR_DATOS, "historico.json")
    hist = json.load(open(ruta, encoding="utf-8")) if os.path.exists(ruta) else []
    idx = {}
    for i, l in enumerate(hist):
        l["_cat"], l["_ep"] = clave(l)
        l["_rem"] = remate(l)
        l["_pal"] = palabras((l.get("titulo") or "") + " " + (l.get("texto") or "")[:300])
        if l["_cat"]:
            idx.setdefault(l["_cat"], []).append(i)
    _CACHE["idx"], _CACHE["hist"] = idx, hist
    return idx, hist


MINIMO_COMPARABLES = 6
MINIMO_PALABRAS = 2


def comparables(lote, tope=50):
    """
    Devuelve (lista, resumen). El resumen va vacio si no hay base suficiente:
    preferimos no decir nada a decir un numero inventado.
    """
    idx, hist = _indice()
    cat, ep = clave(lote)
    if not cat:
        return [], {"motivo": "no se pudo clasificar la categoria"}

    mias = palabras((lote.get("titulo") or "") + " " + (lote.get("texto") or "")[:300])
    if not mias:
        return [], {"motivo": "sin texto suficiente"}

    admitidas = VECINAS.get(ep, set())
    candidatos = []
    for i in idx.get(cat, []):
        c = hist[i]
        if ep and c["_ep"] and c["_ep"] not in admitidas:
            continue
        comunes = len(mias & c["_pal"])
        if comunes >= MINIMO_PALABRAS:
            candidatos.append((comunes, c))
    candidatos.sort(key=lambda x: -x[0])
    sel = candidatos[:tope]

    # precio de remate cuando existe; si no, el de salida, marcado aparte
    remates = [c["_rem"] for _, c in sel if c["_rem"]]
    salidas = [c.get("salida") for _, c in sel if c.get("salida") and not c["_rem"]]
    base, tipo = (remates, "remate") if len(remates) >= MINIMO_COMPARABLES else \
                 ((remates + salidas), "mezcla")

    if len(base) < MINIMO_COMPARABLES:
        return sel, {"motivo": f"solo {len(base)} comparables en '{cat}'"
                               f"{' / ' + ep if ep else ''}, hacen falta {MINIMO_COMPARABLES}",
                     "categoria": cat, "epoca": ep}

    base = sorted(base)
    q = statistics.quantiles(base, n=4) if len(base) >= 4 else [base[0], statistics.median(base), base[-1]]
    r = {"categoria": cat, "epoca": ep, "tipo_precio": tipo, "n": len(base),
         "min": base[0], "p25": q[0], "mediana": statistics.median(base),
         "p75": q[2], "max": base[-1]}

    salida = lote.get("salida") or 0
    if salida:
        r["ratio"] = salida / r["mediana"] if r["mediana"] else None
        if salida <= r["p25"]:
            r["veredicto"] = "por debajo del cuartil bajo"
        elif salida >= r["p75"]:
            r["veredicto"] = "por encima del cuartil alto"
        else:
            r["veredicto"] = "dentro del rango normal"
    return sel, r


def informe(lote, sel, r):
    out = ["", (lote.get("titulo") or "")[:84],
           f"  salida {lote.get('salida', 0):.0f} EUR · {lote.get('casa_nombre', '')}"]
    if "motivo" in r:
        out.append(f"  SIN VEREDICTO: {r['motivo']}")
        return "\n".join(out)
    etq = "remates" if r["tipo_precio"] == "remate" else "remates y salidas mezclados"
    out.append(f"  comparables: {r['n']} lotes de '{r['categoria']}'"
               + (f" / epoca {r['epoca']}" if r["epoca"] else "") + f", por {etq}")
    out.append(f"     min {r['min']:.0f} · p25 {r['p25']:.0f} · MEDIANA {r['mediana']:.0f} "
               f"· p75 {r['p75']:.0f} · max {r['max']:.0f} EUR")
    if "veredicto" in r:
        out.append(f"  -> {r['veredicto']} ({r['ratio']:.2f}x la mediana)")
    for n, c in sel[:3]:
        p = c["_rem"] or c.get("salida") or 0
        marca = "remate" if c["_rem"] else "salida"
        out.append(f"     {p:>6.0f} EUR {marca:<7s} [{n} palabras] {(c.get('titulo') or '')[:54]}")
    return "\n".join(out)


if __name__ == "__main__":
    import encargo
    idx, hist = _indice()
    print(f"Historico: {len(hist)} lotes · categorias: "
          + ", ".join(f"{k} {len(v)}" for k, v in sorted(idx.items(), key=lambda x: -len(x[1]))))
    print("=" * 78)
    for l in encargo.buscar(encargo.CAJONERA_DORMITORIO):
        sel, r = comparables(l)
        print(informe(l, sel, r))
