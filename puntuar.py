# -*- coding: utf-8 -*-
"""
Puntua cada lote contra el perfil de Diego y le pone banderas.

No decide: ordena y avisa. La decision final es de Diego, en la exposicion previa.
Eso sale de la unica cosa en la que coincidieron el marchante suizo, el subastador
y el manual: nadie serio puja sin ver la pieza o pedir el informe de estado.
"""
import re
import unicodedata
from datetime import datetime, timedelta, timezone

import perfil
from casas import CASAS, coste_total


# Palabras completas (no raices) que con limite solo-izquierda saltaban dentro
# de otra palabra: "poster" en "posterior", "lamina" en "laminado", "estampa"
# en "estampado". Verificado: 92 lotes penalizados por error. Permiten el plural.
FIN_PALABRA = {"poster", "lamina", "estampa"}


def _encaja(clave, texto, estricto=False):
    """
    Limite de palabra por la IZQUIERDA siempre que haga falta.

    Sin esto la cosa se llena de falsos positivos reales que vimos auditando:
      'barroc'   saltaba en SUBARROCA (apellido catalan)
      'caliz'    saltaba en "piedra caliza" y en "localiza"
      'santo'    saltaba dentro de otras palabras
    Solo limite izquierdo, porque muchas claves son raices a proposito
    ('religios' tiene que pillar religioso y religiosa).
    """
    if len(clave) <= 4 or any(c.isdigit() for c in clave):
        return re.search(r"(?<![a-z0-9])" + re.escape(clave) + r"(?![a-z0-9])", texto) is not None
    if estricto:
        if clave in FIN_PALABRA:
            return re.search(r"(?<![a-z0-9])" + re.escape(clave) + r"s?(?![a-z])", texto) is not None
        return re.search(r"(?<![a-z0-9])" + re.escape(clave), texto) is not None
    return clave in texto


# En ingles la misma palabra sirve para cosas que no son la pieza: "we do not
# sell reproductions", "reproduction cloth cord", "the style of this sconce",
# "unattributed to a brand". Solo cuenta si no va negada ni habla de una pieza
# suelta (cable, pantalla...).
_NEGADO = re.compile(r"(\bnot?\b|\bnever\b|\bany\b|\bun|rather than|instead of|unlike)\W*(\w+\W+){0,3}$")
_SUELTAS = r"(cord|cable|wir|plug|socket|shade|part|hardware|bulb|knob|handle|print)"
_PIEZA_SUELTA = re.compile(r"^(\W*\w+){0,4}?\W*" + _SUELTAS)
_PIEZA_ANTES = re.compile(_SUELTAS + r"\w*\W+(\w+\W+){0,4}$")
_ESTILO_VAGO = re.compile(r"^\s*(this|my|the|our|your|old|classic|vintage|industrial)\b")


# fuentes que escriben en ingles: ahi "after " es una palabra cualquiera y el
# vocabulario de atribucion es el de GRADOS_ATRIBUCION_EN
EN_INGLES = {"etsy", "1stdibs", "oblist"}

# Formulas de atribucion en espanol que SOLO cuentan en el titulo. En la
# descripcion, "segun la tradicion" o "segun se aprecia" (texto fijo de Odalys)
# y "estilo colorido" son lenguaje corriente, no una confesion de copia.
# Verificado: penalizaban 63 lotes, 52 de ellos arte venezolano de Odalys.
SOLO_TITULO_ES = {"segun ", "estilo "}


def _atribucion_en(formula, texto):
    for m in re.finditer(re.escape(formula), texto):
        antes, despues = texto[max(0, m.start() - 45):m.start()], texto[m.end():m.end() + 25]
        if _NEGADO.search(antes) or _PIEZA_SUELTA.search(despues) or _PIEZA_ANTES.search(antes):
            continue
        if "style of" in formula and _ESTILO_VAGO.search(despues):
            continue
        return True
    return False


def limpiar(s):
    """Minusculas y sin tildes, para que 'oleo' encuentre 'óleo'."""
    s = (s or "").lower()
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


# Solo en el TITULO: lo que no es un mueble aunque nombre uno. En el texto no,
# porque "teak sideboard with brass handles" es un aparador de verdad.
# Salio buscando muebles de guardar en Etsy (2026-10-09): tiradores, maquetas
# para vender laminas, patrones de costura, miniaturas, cajitas.
RE_TITULO_FUERA = re.compile(
    r"\b(drawer|cabinet|wardrobe|dresser|furniture|door)\s+(pulls?|knobs?|handles?|legs?|hardware|caddy|tray)\b"
    r"|\b(knobs?|pulls?)\b.*\b(set of|drawer|cabinet)\b|\bmock-?ups?\b|\bclipart\b|\bprintables?\b"
    r"|\bsewing pattern\b|\bdigital (download|file)\b|\b(svg|png|psd|jpg)\b|\bdoll(house|s)?\b"
    r"|\b1:12\b|\bjunk journal\b|\bposter\b|\bart print\b|\bwall art\b|\btrinket box\b"
    r"|\bring box\b|\bphotography prop\b|\bbackdrop\b|kommodenknopf|m.belgriff|schrankgriff"
    r"|\bmade to order\b|\bcustom (credenza|sideboard|cabinet|dresser)", re.I)


def puntuar(lote):
    txt = limpiar(lote.get("titulo", "") + " " + lote.get("texto", ""))
    pts = 0
    razones, banderas, avisos = [], [], []
    nombres = []        # (clave, puntos) de cada nombre o estilo fuerte encontrado

    # --- artistas por nombre: la senal mas fuerte
    for a in perfil.ARTISTAS:
        if limpiar(a) in txt:
            es_alcanzable = a in perfil.ARTISTAS_ALCANZABLES
            es_venezolano = a in perfil.ARTISTAS_VENEZOLANOS
            p = 8 if es_venezolano else (6 if es_alcanzable else 4)
            pts += p
            nombres.append((a, p))
            razones.append(f"ARTISTA: {a}")
            for clave, aviso in perfil.AVISOS_POR_ARTISTA.items():
                if clave in limpiar(a):
                    avisos.append(aviso)

    # --- gusto
    for k, peso in perfil.GUSTA.items():
        if _encaja(limpiar(k), txt):
            pts += peso
            if peso >= 3:
                razones.append(k)
                nombres.append((k, peso))

    # --- relleno SEO: en las tiendas online (Etsy sobre todo) el vendedor pega
    # una ristra de nombres ("eames, rietveld, cadovius, le corbusier...") que no
    # tienen nada que ver con la pieza. Una pieza de verdad casi nunca nombra a
    # mas de tres. Con cuatro o mas solo cuentan los dos que mas puntuan.
    if lote.get("precio_fijo") and len(nombres) >= 4:
        sobran = sorted((p for _, p in nombres), reverse=True)[2:]
        pts -= sum(sobran)
        banderas.append(f"nombra a {len(nombres)} diseñadores/estilos: suele ser "
                        "relleno para buscadores, no lo que es la pieza")

    # --- rechazo
    descartado = False
    for k, peso in perfil.NO_GUSTA_FUERTE.items():
        if _encaja(limpiar(k), txt, estricto=True):
            pts += peso
            banderas.append(f"NO: {k}")
            if peso <= -4:
                descartado = True
    for k, peso in perfil.NO_GUSTA_SUAVE.items():
        if _encaja(limpiar(k), txt, estricto=True):
            pts += peso

    # --- gran formato: su gusto y la ineficiencia del mercado apuntan igual
    lado = lote.get("lado_mayor_cm") or 0
    if lado >= 150:
        pts += perfil.BONUS_MUY_GRANDE
        razones.append(f"GRAN FORMATO {lado:.0f} cm")
    elif lado >= perfil.GRAN_FORMATO_CM:
        pts += perfil.BONUS_GRAN_FORMATO
        razones.append(f"formato grande {lado:.0f} cm")

    # --- lectura del catalogo: lo que la casa esta diciendo en su codigo
    grados = perfil.GRADOS_ATRIBUCION
    en_ingles = lote.get("casa") in EN_INGLES
    if en_ingles:
        grados = {k: v for k, v in grados.items() if k != "after "}
        grados.update(perfil.GRADOS_ATRIBUCION_EN)
        # "Thonet Style Chair", "Eames style": en el titulo, style = no es suyo
        if re.search(r"[a-z]\s*-?\s*style\b", limpiar(lote.get("titulo", ""))) \
                and "style of " not in txt:
            banderas.append("el titulo dice 'style': al estilo de, NO del disenador")
            pts -= 2
    for formula, significado in grados.items():
        if formula in perfil.GRADOS_ATRIBUCION_EN and en_ingles:
            # "design inspired by 1960s desk lamps" es historia del diseno, no
            # una confesion: "inspired by" solo cuenta en el titulo
            donde = limpiar(lote.get("titulo", "")) if formula == "inspired by" else txt
            if not _atribucion_en(formula, donde):
                continue
        elif formula in SOLO_TITULO_ES:
            if formula not in limpiar(lote.get("titulo", "")):
                continue
        elif formula not in txt:
            continue
        banderas.append(f"'{formula.strip()}' = {significado}")
        pts -= 2

    # --- firma: multiplica el precio por 3 o 4
    if any(f in txt for f in perfil.FIRMA_MALA):
        banderas.append("FIRMA EN PLANCHA: leelo como SIN FIRMA, vale como estampa decorativa")
        pts -= 3
    elif any(f in txt for f in perfil.FIRMA_BUENA):
        pts += 2
        razones.append("firmado a lapiz")

    # --- lote reciclado: no se vendio, luego es negociable o va a bajar
    if lote.get("no_vendido"):
        razones.append("NO VENDIDO: candidato a rebaja")
        pts += 2
        if CASAS.get(lote["casa"], {}).get("relanza_40"):
            banderas.append("Segre relanza a -40 %: espera en vez de comprar ahora")

    # --- bajada de precio ya detectada entre pasadas
    hist = lote.get("historico_salida") or []
    for h in hist:
        if h["a"] < h["de"]:
            baja = 100 * (1 - h["a"] / h["de"])
            razones.append(f"BAJO DE PRECIO {baja:.0f} % ({h['de']:.0f} -> {h['a']:.0f} EUR)")
            pts += 4

    # --- rebaja que anuncia la propia tienda (Pamono marca el precio anterior)
    antes = lote.get("precio_anterior")
    if antes and lote.get("salida") and antes > lote["salida"]:
        baja = 100 * (1 - lote["salida"] / antes)
        razones.append(f"BAJO DE PRECIO {baja:.0f} % en la tienda ({antes:.0f} -> {lote['salida']:.0f} EUR)")
        pts += 3

    # --- presupuesto
    salida = lote.get("salida") or 0
    fuera_presupuesto = False
    if salida and salida > perfil.PRECIO_MAX:
        if salida <= perfil.PRECIO_MAX_ESTIRANDO and pts >= 12:
            banderas.append(f"Por encima de presupuesto ({salida:.0f} EUR) pero encaja mucho")
        else:
            fuera_presupuesto = True
    if salida and salida < perfil.PRECIO_MIN:
        pts -= 1

    lote["puntos"] = pts
    lote["razones"] = razones
    lote["banderas"] = banderas
    # avisos que trae la propia fuente (Etsy: nuevo/no vintage, envio fuera de
    # la UE, moneda distinta) van delante de los del perfil
    lote["avisos"] = list(lote.get("avisos_fuente") or []) + avisos
    if lote.get("vintage") is False:
        banderas.insert(0, "pieza NUEVA, no vintage")
    if RE_TITULO_FUERA.search(lote.get("titulo") or ""):
        banderas.append("NO: accesorio, lamina o miniatura, no un mueble")
        descartado = True
    lote["descartado"] = descartado or fuera_presupuesto
    # "rechazado" = choca de frente con su gusto (religioso, joyeria, vino...).
    # Va aparte del presupuesto: la pagina tiene su propio filtro de precio y
    # no debe perder un lote solo porque pase de 600 EUR.
    lote["rechazado"] = descartado

    if salida:
        _, desglose = coste_total(salida, lote["casa"])
        lote["coste"] = desglose
    return lote


def vigente(l, dias=4):
    """
    Una tienda no avisa cuando vende algo: la pieza simplemente desaparece del
    listado. Si una pieza de precio fijo lleva mas de `dias` sin aparecer en
    ninguna pasada, se da por vendida y sale de la pagina.
    """
    if l.get("historico"):
        return False
    # Alcala marca en el titulo lo que ya se adjudico: "VENDIDO 1052. Comoda..."
    # ("NO VENDIDO" no empieza asi y se queda: es candidato a rebaja)
    if re.match(r"\s*vendido\b", l.get("titulo") or "", re.I):
        return False
    # Etsy deja anuncios ya vendidos como "SOLD - example only" a 0 EUR
    if re.search(r"^\W*(now\s+)?sold\b|do not purchase", l.get("titulo") or "", re.I):
        return False
    # Pamono pone 2 o 3 EUR a las piezas sin precio publico: no son gangas
    if l.get("casa") == "pamono" and (l.get("salida") or 0) < 20:
        return False
    # Etsy y eBay caducan por su cuenta: su archivo se rehace en cada pasada y
    # vista.py lo descarta entero cuando es viejo (24 h y 6 h)
    if not l.get("precio_fijo") or l.get("casa") in ("etsy", "ebay"):
        return True
    try:
        visto = datetime.fromisoformat(l["visto"])
    except (KeyError, ValueError):
        return True
    return datetime.now(timezone.utc) - visto < timedelta(days=dias)


def ranking(lotes, minimo=4):
    lotes = [l for l in lotes if vigente(l)]
    puntuados = [puntuar(dict(l)) for l in lotes]
    vivos = [l for l in puntuados if not l["descartado"] and l["puntos"] >= minimo]
    return sorted(vivos, key=lambda l: (-l["puntos"], l.get("salida") or 0))


def todos_los_vivos(lotes):
    """
    Para la pagina: TODO lo que esta a la venta y no choca de frente con su
    gusto, puntue lo que puntue. Un encargo concreto ("comoda blanca") tiene
    que poder encontrar piezas que el perfil de gusto no habria subido nunca.
    """
    lotes = [l for l in lotes if vigente(l)]
    puntuados = [puntuar(dict(l)) for l in lotes]
    vivos = [l for l in puntuados if not l["rechazado"]]
    return sorted(vivos, key=lambda l: (-l["puntos"], l.get("salida") or 0))


def ficha(l):
    """Una ficha legible, con el coste real y no solo el martillo."""
    out = []
    out.append(f"[{l['puntos']:+3d}] {l['casa_nombre']} lote {l.get('lote') or '?'}")
    out.append(f"      {l['titulo'][:95]}")
    c = l.get("coste")
    if c:
        out.append(f"      salida {c['martillo']:.0f} EUR  ->  TOTAL REAL {c['total']:.0f} EUR "
                   f"(+{c['recargo_pct']:.0f} %)  sin contar transporte")
    if l["razones"]:
        out.append(f"      a favor: {', '.join(l['razones'][:5])}")
    for b in l["banderas"][:3]:
        out.append(f"      OJO: {b}")
    for a in l["avisos"][:1]:
        out.append(f"      AVISO: {a}")
    out.append(f"      {l['url']}")
    return "\n".join(out)
