# -*- coding: utf-8 -*-
"""
Genera datos/vista.html (Caxi-Vaxi): la rejilla visual para escanear cientos de lotes rapido.

Decisiones que vienen del brief de Diego:
  - La imagen manda. Todo lo demas es cartela.
  - Puntuaciones SEPARADAS (gusto, oportunidad, logistica, confianza), nunca
    una sola nota opaca.
  - Lo desconocido se queda desconocido. No se inventa envio ni condicion.
  - El feedback se guarda y se exporta, para que vuelva al perfil.

La plantilla HTML vive en plantilla.py.
"""
import json
import warnings
warnings.simplefilter('ignore')
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from casas import CASAS
from encargo import dimensiones
from plantilla import PLANTILLA
from puntuar import ranking, todos_los_vivos
import ebay
import wallapop
from etsy import cargar_si_fresco
from scraper import DIR_DATOS, despegar_br


# --------------------------------------------------------------------------
# Puntuaciones separadas
# --------------------------------------------------------------------------
def escalar(v, tope):
    return max(0, min(100, round(100 * v / tope))) if tope else 0


def puntuaciones(l):
    gusto = escalar(l.get("puntos", 0), 20)

    # Oportunidad: no vendido, bajada de precio, salida baja. NUNCA decimos
    # "infravalorado" sin evidencia: eso necesita comparables de verdad.
    op, por_que = 0, []
    if l.get("no_vendido"):
        op += 30
        por_que.append("no se vendio")
    for r in l.get("razones", []):
        if "BAJO DE PRECIO" in r:
            op += 40
            por_que.append("ya bajo de precio")
    salida = l.get("salida") or 0
    if 0 < salida <= 150:
        op += 20
        por_que.append("salida baja")
    elif 150 < salida <= 400:
        op += 10
    if CASAS.get(l.get("casa"), {}).get("relanza_40") and l.get("no_vendido"):
        op += 15
        por_que.append("Segre relanza a -40 %")
    op = min(100, op)

    # Logistica: cuanto cuesta de verdad traerlo a casa
    log = 50
    casa = CASAS.get(l.get("casa"))
    if l.get("precio_fijo"):
        log += 20                       # tienda: sin prima ni plazo de retirada
    if casa:
        log += int((0.25 - casa["comision"]) * 200)
        if casa.get("almacenaje_dia"):
            log -= 10                   # penalizacion por retirada a reloj
    if (l.get("ubicacion") or "").lower().startswith("caracas"):
        log = 5                         # importacion desde Venezuela
    lado = l.get("lado_mayor_cm") or 0
    if lado >= 180:
        log -= 15                       # no entra en un coche
    log = max(0, min(100, log))

    # Confianza: cuanto nos fiamos de lo que hemos extraido
    conf = 30
    if l.get("lado_mayor_cm"):
        conf += 25
    if l.get("imagen"):
        conf += 15
    if len(l.get("texto") or "") > 200:
        conf += 15
    if l.get("banderas"):
        conf -= 10                      # el catalogo admite algo raro
    conf = max(0, min(100, conf))

    return {"gusto": gusto, "oportunidad": op, "logistica": log,
            "confianza": conf, "op_por_que": por_que}


MATERIALES = ["roble", "nogal", "teca", "palisandro", "pino", "haya", "cerezo",
              "caoba", "bronce", "marmol", "hierro", "acero", "laton", "ceramica",
              "cristal", "vidrio", "mimbre", "enea", "cuero", "formica", "metal"]
PERIODOS = [("1950", r"\b195\d|a[nñ]os 50\b|\b50s\b"), ("1960", r"\b196\d|a[nñ]os 60\b|\b60s\b"),
            ("1970", r"\b197\d|a[nñ]os 70\b|\b70s\b"), ("1980", r"\b198\d|a[nñ]os 80\b|\b80s\b"),
            ("s. XIX", r"s\.?\s*xix|siglo xix"), ("s. XVIII", r"s\.?\s*xviii|siglo xviii")]


COLORES = [
    ("blanco", r"blanc[oa]s?|white"),
    ("negro", r"negr[oa]s?|black|ebonizad[oa]"),
    ("gris", r"gris(es)?|grey|gray"),
    ("rojo", r"roj[oa]s?|granate|burdeos|\bred\b"),
    ("azul", r"azul(es)?|blue"),
    ("verde", r"verdes?|green"),
    ("amarillo", r"amarill[oa]s?|mostaza|yellow"),
    ("naranja", r"naranjas?|orange"),
    ("marron", r"marron(es)?|brown"),
    ("dorado", r"dorad[oa]s?|gold(en)?"),
    ("cromado", r"cromad[oa]s?|niquelad[oa]|chrome"),
]


def sin_tildes(s):
    import unicodedata
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def descripcion(l):
    """Texto del catalogo, limpio y corto, para leerlo en la ficha y buscar en el."""
    t = re.sub(r"\s+", " ", l.get("texto") or "").strip()
    tit = (l.get("titulo") or "").strip()
    if tit and t.lower().startswith(tit.lower()[:40]):
        t = t[len(tit):].lstrip(" .-")
    t = re.sub(r"\b(NO DISPONIBLE|NO VENDIDO|VENDIDO|COMPRAR|Precio salida)\b.*$", "", t).strip()
    return t[:320]


def atributos(l):
    t = ((l.get("titulo") or "") + " " + (l.get("texto") or "")).lower()
    plano = sin_tildes(t[:700])
    mats = [m for m in MATERIALES if m in t]
    per = [p for p, rx in PERIODOS if re.search(rx, t)]
    dims = dimensiones(l.get("texto") or "")
    cols = [c for c, rx in COLORES
            if re.search(r"(?<![a-z])(" + rx + r")(?![a-z])", plano)]
    return {
        "colores": cols,
        "materiales": mats[:3],
        "periodo": per[0] if per else None,
        "dims": " x ".join(f"{v:.0f}" for v in dims[0]) + " cm" if dims else None,
        # las tres medidas ordenadas de mayor a menor, para filtrar por ancho,
        # alto y fondo por separado en el buscador de la pagina
        "d3": [round(v) for v in dims[0]] if dims else None,
        "ubicacion": l.get("ubicacion") or ("Madrid" if l.get("casa") in CASAS else None),
    }


# --------------------------------------------------------------------------
# Donde esta la pieza: pais normalizado (ISO) y una etiqueta legible
# --------------------------------------------------------------------------
PAISES = {
    "ES": "España", "FR": "Francia", "DE": "Alemania", "IT": "Italia", "NL": "Países Bajos",
    "BE": "Bélgica", "PT": "Portugal", "GB": "Reino Unido", "IE": "Irlanda", "DK": "Dinamarca",
    "SE": "Suecia", "NO": "Noruega", "FI": "Finlandia", "AT": "Austria", "CH": "Suiza",
    "PL": "Polonia", "CZ": "Chequia", "HU": "Hungría", "GR": "Grecia", "LU": "Luxemburgo",
    "SK": "Eslovaquia", "SI": "Eslovenia", "HR": "Croacia", "RO": "Rumanía", "BG": "Bulgaria",
    "EE": "Estonia", "LV": "Letonia", "LT": "Lituania", "MT": "Malta", "CY": "Chipre",
    "MC": "Mónaco", "IS": "Islandia", "RS": "Serbia", "UA": "Ucrania", "TR": "Turquía",
    "US": "Estados Unidos", "CA": "Canadá", "VE": "Venezuela", "MX": "México", "AR": "Argentina",
    "BR": "Brasil", "GB-": "Reino Unido", "AU": "Australia", "JP": "Japón", "CN": "China",
    "IN": "India", "IL": "Israel", "ZA": "Sudáfrica",
}
EUROPA = {"ES", "FR", "DE", "IT", "NL", "BE", "PT", "GB", "IE", "DK", "SE", "NO", "FI", "AT", "CH",
          "PL", "CZ", "HU", "GR", "LU", "SK", "SI", "HR", "RO", "BG", "EE", "LV", "LT", "MT", "CY",
          "MC", "IS", "RS", "UA"}
_POR_NOMBRE = {sin_tildes(v).lower(): k for k, v in PAISES.items()}
_POR_NOMBRE.update({"holanda": "NL", "paises bajos": "NL", "inglaterra": "GB", "reino unido": "GB",
                    "estados unidos": "US", "usa": "US", "república checa": "CZ", "republica checa": "CZ"})
# Fuentes que solo venden desde un pais
PAIS_DE_FUENTE = {"wallapop": "ES", "labasilica": "ES", "alcala": "ES", "salaretiro": "ES",
                  "segre": "ES", "ansorena": "ES", "duran": "ES"}
CIUDADES = {"caracas": "VE", "miami": "US", "madrid": "ES", "barcelona": "ES", "terrassa": "ES"}


def pais(l):
    """ISO del pais donde esta la pieza, o None si la fuente no lo dice."""
    casa = l.get("casa")
    if casa in PAIS_DE_FUENTE:
        return PAIS_DE_FUENTE[casa]
    u = (l.get("ubicacion") or "").strip()
    if re.fullmatch(r"[A-Z]{2}", u):
        return u
    bajo = sin_tildes(u).lower()
    if bajo in _POR_NOMBRE:
        return _POR_NOMBRE[bajo]
    for ciudad, iso in CIUDADES.items():
        if bajo.startswith(ciudad):
            return iso
    return None


def ubicacion_txt(l, iso):
    """'Madrid, España', 'Francia' o None. Nada de basura del catalogo."""
    nombre = PAISES.get(iso) if iso else None
    u = (l.get("ubicacion") or "").strip()
    if l.get("casa") in CASAS:
        return "Madrid, España"
    if not u or re.fullmatch(r"[A-Z]{2}", u) or sin_tildes(u).lower() in _POR_NOMBRE:
        return nombre
    ciudad = re.split(r"\s{1,}(?=[A-ZÁÉÍÓÚ]{3,})|[,(]", u)[0].strip()[:30]
    if not nombre or sin_tildes(ciudad).lower() == sin_tildes(nombre).lower():
        return ciudad or nombre
    return f"{ciudad}, {nombre}"


def sin_gritos(t):
    """
    "SILLAS CANTILEVER S78 DE THONET" -> "Sillas cantilever S78 de Thonet".
    Un titulo casi todo en mayusculas se lee mal en la rejilla. Se baja a
    minusculas y se respetan los codigos (S78, MB15) y los nombres propios
    que la propia frase trae con mayuscula inicial... que en mayusculas no se
    distinguen, asi que solo se recupera la primera letra.
    """
    letras = [c for c in t if c.isalpha()]
    if len(letras) < 8 or sum(c.isupper() for c in letras) / len(letras) < 0.7:
        return t
    palabras = []
    for w in t.split():
        palabras.append(w if re.search(r"\d", w) else w.lower())
    out = " ".join(palabras)
    # mayuscula al empezar y despues de cada punto
    return re.sub(r"(^|[.!?]\s+)([a-záéíóúñü])", lambda m: m.group(1) + m.group(2).upper(), out)


def ano_txt(l, periodo):
    """'Años 60', 's. XIX' o la epoca que da la fuente."""
    if l.get("epoca_etsy"):
        e = l["epoca_etsy"]
        return re.sub(r"^(\d{2})(\d)0s$", lambda m: f"Años {m.group(2)}0" if m.group(1) == "19" else e, e)
    if periodo and re.fullmatch(r"19\d0", periodo):
        return f"Años {periodo[2:]}"
    return periodo


DIR_MARCA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "marca")


def svg(nombre):
    """El SVG de la mascota, listo para meterlo en linea (sin comentarios)."""
    t = open(os.path.join(DIR_MARCA, nombre), encoding="utf-8").read()
    return re.sub(r"\s*<!--.*?-->", "", t, flags=re.S).strip()


def favicon():
    from urllib.parse import quote
    t = (svg("cachalote.svg").replace("currentColor", "#0A0A0B")
         .replace("var(--hueco,#2e4a52)", "#FFFFFF"))
    return "data:image/svg+xml," + quote(t)


RE_THUMB = re.compile(r"/img/thumbs/\d+/")


def fotos(url):
    """
    Devuelve (foto para la rejilla, foto grande para el detalle).

    El scraper guarda la miniatura de 260 px del listado, y por eso todo se veia
    borroso. Las cinco casas sirven la misma imagen a 500 px en /thumbs/500/ y
    el original entero quitando /thumbs/NNN/ (comprobado el 2026-10-02).
    Shopify redimensiona con ?width=.
    """
    if not url:
        return None, None
    if "etsystatic.com" in url:
        return url, None            # la grande viene aparte en imagen_grande
    if RE_THUMB.search(url):
        return RE_THUMB.sub("/img/thumbs/500/", url), RE_THUMB.sub("/img/", url)
    if "cdn.shopify.com" in url:
        sep = "&" if "?" in url else "?"
        return url + sep + "width=600", url + sep + "width=1600"
    return url, url


def preparar(lotes):
    out = []
    for l in lotes:
        s = puntuaciones(l)
        a = atributos(l)
        c = l.get("coste") or {}
        chica, grande = fotos(l.get("imagen"))
        grande = l.get("imagen_grande") or grande
        iso = pais(l)
        out.append({
            "id": l["url"],
            "fuente": l["casa_nombre"],
            # para el desplegable: todo Etsy junto, no 1.400 tiendas sueltas
            "grupo": "Etsy" if l.get("casa") == "etsy" else l["casa_nombre"],
            # eBay va aparte (su licencia prohibe mezclarlo con otras fuentes) y
            # la pagina lo oculta cuando la consulta pasa de 6 h
            "aparte": l.get("casa") == "ebay",
            "obt": l.get("obtenido") if l.get("casa") == "ebay" else None,
            "res": bool(l.get("reservado")),
            "nuevo": bool(l.get("nuevo_de_vendedor")),
            "lote": l.get("lote"),
            "titulo": sin_gritos(despegar_br(l.get("titulo") or "sin titulo", l.get("texto")))[:140],
            "salida": l.get("salida"),
            "total": c.get("total"),
            "recargo": c.get("recargo_pct"),
            "img": chica,
            "imgG": grande,
            "url": l["url"],
            "dims": a["dims"],
            "d3": a["d3"],
            "lado": round(l.get("lado_mayor_cm") or 0),
            "mats": a["materiales"],
            "col": a["colores"],
            "desc": descripcion(l),
            "periodo": a["periodo"],
            "donde": a["ubicacion"],
            "nov": bool(l.get("no_vendido")),
            "fijo": bool(l.get("precio_fijo")),
            "g": s["gusto"], "o": s["oportunidad"],
            "lg": s["logistica"], "cf": s["confianza"],
            "porque": l.get("razones", [])[:4],
            "riesgos": l.get("banderas", [])[:3],
            "avisos": l.get("avisos", [])[:2],
            "orig": l.get("precio_original"),
            "epoca": l.get("epoca_etsy"),
            "opq": s["op_por_que"],
            # lo que ensena la ficha nueva: solo hechos de la pieza
            "pais": iso,
            "eu": iso in EUROPA if iso else None,
            "lugar": ubicacion_txt(l, iso),
            "ano": ano_txt(l, a["periodo"]),
            "envio": l.get("envio"),
            "antes": l.get("precio_anterior") if (l.get("precio_anterior") or 0) > (l.get("salida") or 0) else None,
            "alta": l.get("primera_vez") or l.get("visto"),
        })
    return out


# Busquedas con nombre: cada una deja un archivo en datos/ que abre la pagina
# con la busqueda puesta (open datos/muebles-de-guardar.html). La sintaxis es
# la del enlace: vista.html#tipos=almacenaje&tope=
ATAJOS = {
    "muebles-de-guardar": "tipos=almacenaje&tope=",
}


def escribir_atajos():
    for nombre, busqueda in ATAJOS.items():
        with open(os.path.join(DIR_DATOS, nombre + ".html"), "w", encoding="utf-8") as f:
            f.write('<!doctype html><meta charset="utf-8"><title>Caxi-Vaxi</title>'
                    f'<meta http-equiv="refresh" content="0;url=vista.html#{busqueda}">'
                    f'<a href="vista.html#{busqueda}">Abrir la busqueda</a>')


def construir(minimo=None):
    """
    Por defecto entra TODO lo que esta a la venta y no choca con su gusto: asi
    un encargo concreto encuentra piezas aunque el perfil no las puntue.
    Con un minimo (p. ej. `vista.py 1`) entra solo lo que encaja con el perfil.
    """
    ruta = os.path.join(DIR_DATOS, "lotes.json")
    lotes = json.load(open(ruta, encoding="utf-8")) if os.path.exists(ruta) else []
    # Etsy va aparte y solo entra si tiene menos de 24 h (condiciones de su API)
    de_etsy, estado_etsy = cargar_si_fresco()
    print(f"  {estado_etsy}: {len(de_etsy)} anuncios")
    lotes = lotes + de_etsy
    # eBay, solo si la consulta tiene menos de 6 h (licencia de su API)
    de_ebay, estado_ebay = ebay.cargar_si_fresco()
    print(f"  {estado_ebay}: {len(de_ebay)} anuncios")
    # Wallapop: la ultima pasada, sin lo vendido
    de_wallapop, estado_wallapop = wallapop.cargar()
    print(f"  {estado_wallapop}: {len(de_wallapop)} anuncios")
    # Lo reservado en Wallapop no interesa: casi nunca vuelve a estar libre
    lotes = lotes + de_ebay + [l for l in de_wallapop if not l.get("reservado")]
    elegidos = ranking(lotes, minimo=minimo) if minimo is not None else todos_los_vivos(lotes)
    # Solo Europa: lo que se sabe que esta fuera (Odalys Caracas, tiendas de
    # Etsy en EE. UU.) no entra. Lo que no dice su pais se queda.
    datos = [d for d in preparar(elegidos) if d["eu"] is not False]
    # "</" dentro del JSON cerraria la etiqueta <script> si un titulo lo trae
    carga = json.dumps(datos, ensure_ascii=False).replace("</", "<\\/")
    html = (PLANTILLA.replace("__BALLENA__", svg("cachalote.svg"))
            .replace("__BALLENA_CACHARROS__", svg("cachalote_cacharros.svg"))
            .replace("__FAVICON__", favicon()))
    html = html.replace("__DATOS__", carga)
    html = html.replace("__FECHA__", datetime.now().strftime("%d/%m/%Y %H:%M"))
    vivos = sum(1 for l in lotes if not l.get("historico"))
    html = html.replace("__TOTAL__", f"{vivos:,}".replace(",", "."))
    salida = os.path.join(DIR_DATOS, "vista.html")
    with open(salida, "w", encoding="utf-8") as f:
        f.write(html)
    escribir_atajos()
    return salida, len(datos), len(lotes)


if __name__ == "__main__":
    minimo = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else None
    ruta, mostrados, total = construir(minimo)
    print(f"{ruta}\n  {mostrados} lotes en la rejilla, de {total} leidos")
