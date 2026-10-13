# -*- coding: utf-8 -*-
"""
Wallapop, SOLO por las paginas que su robots.txt permite.

Revisado el 2026-10-13:
  - robots.txt prohibe /search, /app/ y cualquier URL con "?". Permite el resto:
    fichas (/item/<slug>), perfiles (/user/<slug>) y las portadas tematicas que
    Wallapop publica para buscadores (/muebles-deco-y-jardin/<tema>/<ciudad>).
  - Las tres paginas traen sus datos en <script id="__NEXT_DATA__">. No hay que
    ejecutar JavaScript ni tocar la API.
  - La API de busqueda (api.wallapop.com/api/v3/search) solo responde si uno se
    hace pasar por Chrome. Eso es saltarse una proteccion: NO se usa.
  - Sus condiciones (3.1.2, puntos 15 y 17) prohiben los bots aunque robots.txt
    deje. Diego asume ese riesgo para uso personal y moderado.

Lo que se lee, fijado a mano en config_local.py:
    WALLAPOP_ARTICULOS  = ["aparador-danes-...-1312536858", ...]  piezas guardadas
    WALLAPOP_VENDEDORES = ["jesusf-14536777", ...]                vendedores vigilados
    WALLAPOP_PORTADAS   = ["muebles-deco-y-jardin/aparador-mid-century/madrid", ...]
Si WALLAPOP_PORTADAS no esta, se usan las de PORTADAS, abajo.

Limites: una pasada al dia, como mucho TOPE_PAGINAS (80) paginas, 3 s entre
peticiones (scraper.traer) y parada total ante un 403.

Un perfil muestra sus primeros 40 anuncios. Los siguientes se piden con "?" o
por la API, y las dos cosas estan fuera: de un vendedor grande solo se ve eso.

Cada pasada SOBRESCRIBE datos/wallapop.json y lo compara con la anterior para
marcar cambios: bajada de precio, reservado, vendido o desaparecido, y anuncio
nuevo de un vendedor vigilado.

Uso:
    .venv/bin/python wallapop.py               la pasada diaria
    .venv/bin/python wallapop.py --descubrir   prueba las portadas que sugieren
                                               las ya leidas y suma las que existen
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from encargo import dimensiones
from etsy import medidas_de_texto
from scraper import DIR_DATOS, ParadaTotal, traer
from tiendas import TOPE_EUR, lote, medidas_txt

WEB = "https://es.wallapop.com"
ARCHIVO = os.path.join(DIR_DATOS, "wallapop.json")
TOPE_PAGINAS = 80     # 38 vendedores + portadas; a 3 s son unos 4 minutos al dia

# Portadas tematicas de Wallapop para Madrid. Cada una trae 80 anuncios.
# Wallapop solo las crea para busquedas populares: "silla thonet" o "busto" no
# tienen (comprobado el 2026-10-13, tambien sin ciudad). Estas existen.
PORTADAS = [
    "muebles-deco-y-jardin/aparador-mid-century/madrid",
    "muebles-deco-y-jardin/aparador-vintage/madrid",
    "muebles-deco-y-jardin/aparador-retro/madrid",
    "muebles-deco-y-jardin/mueble-vintage/madrid",
    "muebles-deco-y-jardin/mueble-bar-vintage/madrid",
    "muebles-deco-y-jardin/comoda-antigua-de-madera/madrid",
    "muebles-deco-y-jardin/cajonera-vintage/madrid",
    "muebles-deco-y-jardin/armario-vintage/madrid",
    "muebles-deco-y-jardin/escritorio-vintage/madrid",
    "muebles-deco-y-jardin/mesa-auxiliar-vintage/madrid",
    "muebles-deco-y-jardin/sillas-vintage/madrid",
    "muebles-deco-y-jardin/sillon-vintage/madrid",
    "muebles-deco-y-jardin/flexo-vintage/madrid",
    "muebles-deco-y-jardin/espejo-vintage/madrid",
    "muebles-deco-y-jardin/escultura/madrid",
]
# Las que se descubren siguiendo sus "busquedas relacionadas" (wallapop.py
# --descubrir) se guardan aqui y entran solas en la pasada diaria.
DESCUBIERTAS = os.path.join(DIR_DATOS, "wallapop_portadas.json")
# De las sugeridas, solo se prueban las que suenan a su gusto
RE_SUGERIDA_SI = re.compile(r"vintage|retro|mid-century|antigu|teca|nogal|palisandro|industrial|art-deco|"
                            r"bauhaus|diseno|danes|nordic|escandinav|brutalista|racionalista|chillida|secreter|"
                            r"bureau|anos-[5-8]0|ceramica|bronce|marmol|laton|mimbre|ratan")
RE_SUGERIDA_NO = re.compile(r"ikea|malm|alex|micke|hemnes|maison|rustic|provenzal|chino|blanc|clasic|infantil|"
                            r"bebe|juguete|oficina|ordenador|garaje|herramienta|resina|cocina|bano|exterior|"
                            r"terraza|plastico|nuevo|jesus|maria|virgen|cristo|santo|buda|religios|dorad")

RE_NEXT = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)
RE_SLUG = re.compile(r"^[a-z0-9-]+$")
RE_RUTA = re.compile(r"^[a-z0-9-]+(?:/[a-z0-9-]+){1,2}$")


def ahora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def listas():
    """Las tres listas de config_local.py, ya limpias."""
    try:
        import config_local as c
    except ImportError:
        c = None

    def lista(nombre, defecto, patron):
        v = getattr(c, nombre, None) if c else None
        v = defecto if v is None else v
        # se aceptan URLs enteras pegadas desde el navegador
        limpio = []
        for x in v:
            x = x.strip().split("?")[0].rstrip("/")
            x = re.sub(r"^https?://[^/]+/", "", x)
            x = re.sub(r"^(item|user)/", "", x)
            if patron.match(x):
                limpio.append(x)
            else:
                print(f"  WALLAPOP: se ignora {x!r} en {nombre}: no parece una direccion valida")
        return limpio

    portadas = PORTADAS + [x for x in descubiertas() if x not in PORTADAS]
    return (lista("WALLAPOP_ARTICULOS", [], RE_SLUG),
            lista("WALLAPOP_VENDEDORES", [], RE_SLUG),
            lista("WALLAPOP_PORTADAS", portadas, RE_RUTA))


def descubiertas():
    try:
        return json.load(open(DESCUBIERTAS, encoding="utf-8"))
    except (OSError, ValueError):
        return []


def datos_pagina(h):
    """El JSON de __NEXT_DATA__ -> props.pageProps, o None."""
    m = RE_NEXT.search(h or "")
    if not m:
        return None
    try:
        return json.loads(m.group(1))["props"]["pageProps"]
    except (ValueError, KeyError, TypeError):
        return None


def _texto(v):
    """Wallapop da a veces {'original': ..., 'translated': ...} y a veces texto."""
    if isinstance(v, dict):
        return v.get("original") or v.get("translated") or ""
    return v or ""


def _precio(v):
    """1620 | {'amount': 1620} | {'cash': {'amount': 1620}} -> 1620.0"""
    if isinstance(v, dict):
        v = (v.get("cash") or v).get("amount")
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _foto(imagenes):
    """(rejilla, detalle). Las de Wallapop se piden por tamano con pictureSize."""
    if not imagenes:
        return None, None
    i = imagenes[0]
    urls = i.get("urls") or {}
    base = urls.get("big") or urls.get("medium") or i.get("smallUrl") or urls.get("small")
    if not base:
        return None, None
    base = base.split("?")[0]
    return base + "?pictureSize=W640", base + "?pictureSize=W800"


# "Medidas: 190cm ancho x 42cm fondo x 78cm alto", "1,10 m de alto": en Wallapop
# el numero va delante del eje, al reves de lo que espera medidas_de_texto
RE_NUM_EJE = re.compile(
    r"(\d{1,3}(?:[.,]\d{1,2})?)\s*(cm|mm|m|metros?)?\.?\s*(?:de\s+)?"
    r"(ancho|anchura|largo|longitud|alto|altura|fondo|profundidad)\b", re.I)
EJE_ES = {"ancho": "ancho", "anchura": "ancho", "largo": "ancho", "longitud": "ancho",
          "alto": "alto", "altura": "alto", "fondo": "fondo", "profundidad": "fondo"}


def medidas_num_eje(texto):
    out = {}
    for m in RE_NUM_EJE.finditer(texto or ""):
        v = float(m.group(1).replace(",", "."))
        u = (m.group(2) or "cm").lower()
        v *= 100 if u.startswith("m") and u != "mm" else (0.1 if u == "mm" else 1)
        if 2 < v < 400:
            out.setdefault(EJE_ES[m.group(3).lower()], round(v))
    return out


def sin_etiquetas(desc):
    """
    Quita el parrafo de etiquetas para buscadores que muchos vendedores pegan al
    final: "Space age, minimalista, retro, Art deco, Mid Century, escandinavo,
    nordico, vintage, Gplan, Danish...". Una frase con seis o mas trozos
    separados por comas, casi todos de una a tres palabras, no describe la
    pieza. Lo que va detras de "tags:" o "etiquetas:" tampoco.
    """
    desc = RE_TAGS.split(desc or "", maxsplit=1)[0]
    buenos = []
    for par in desc.split("\n"):
        frases = [f for f in re.split(r"(?<=[.!?])\s+", par) if not _es_lista(f)]
        if frases:
            buenos.append(" ".join(frases))
    return "\n".join(buenos)


RE_TAGS = re.compile(r"\b(?:tags|etiquetas|palabras clave)\s*:", re.I)


def _es_lista(frase):
    trozos = [t.strip() for t in frase.split(",") if t.strip()]
    cortos = sum(1 for t in trozos if len(t.split()) <= 3)
    return len(trozos) >= 6 and cortos >= 0.8 * len(trozos)


def medidas_libres(texto):
    """
    Medidas escritas a mano, de mas a menos explicito: "190cm ancho x 42cm
    fondo", "Breite: 120 cm" y por ultimo "45 x 50 x 85 cm", que no dice que
    eje es cual. Devuelve ('190 x 42 x 78 cm', 190) o ('', 0).
    """
    m = medidas_num_eje(texto)
    if len(m) < 2:
        m = medidas_de_texto(texto)
    if len(m) >= 2:
        return medidas_txt(m)
    d = dimensiones(texto)
    if d:
        return " x ".join(f"{v:.0f}" for v in d[0]) + " cm", round(d[0][0])
    return "", 0


def _medidas(medidas, texto):
    """El campo measures si viene relleno; si no, lo que diga la descripcion."""
    m = {}
    if isinstance(medidas, dict):
        for eje, campo in (("ancho", "width_cm"), ("alto", "height_cm"), ("fondo", "length_cm")):
            try:
                v = float(medidas.get(campo) or 0)
            except (TypeError, ValueError):
                v = 0
            if v:
                m[eje] = v
    if len(m) >= 2:
        return medidas_txt(m)
    return medidas_libres(texto)


def registro(d, via, vendedor=None, ciudad=None):
    """
    Normaliza un anuncio venga de donde venga. Las tres paginas lo escriben
    distinto: la ficha trae flags y price.cash, la portada sold/reserved y un
    precio suelto, el perfil isReserved y price.amount.
    """
    slug = d.get("slug") or d.get("slugId")
    precio = _precio(d.get("price"))
    if not slug or precio is None:
        return None
    flags = d.get("flags") or {}
    reservado = bool(flags.get("reserved") or flags.get("onHold") or d.get("reserved")
                     or d.get("isReserved"))
    vendido = bool(flags.get("sold") or flags.get("expired") or d.get("sold"))
    titulo = _texto(d.get("title")).strip()
    desc = re.sub(r"\s+", " ", sin_etiquetas(_texto(d.get("description")))).strip()
    dims, lado = _medidas(d.get("measures"), desc)
    rasgos = d.get("characteristics") or ""      # "Buen estado · Marron · Madera"
    loc = d.get("location") or {}
    chica, grande = _foto(d.get("images"))
    texto = " . ".join(x for x in (titulo, dims, rasgos, desc[:900]) if x)
    vend = vendedor or (d.get("seller") or {}).get("slug")
    return lote(
        "wallapop", "Wallapop", titulo, f"{WEB}/item/{slug}", precio,
        lote=slug.rsplit("-", 1)[-1], texto=texto[:1500], imagen=chica,
        imagen_grande=grande, origen=f"wallapop-{via}", lado_mayor_cm=lado,
        ubicacion=loc.get("city") or ciudad, reservado=reservado, vendido=vendido,
        vendedor=vend, via=via,
    )


def leer_articulo(slug):
    """None si la ficha ya no existe (404): borrada o vendida y retirada."""
    p = datos_pagina(traer(f"{WEB}/item/{slug}"))
    if not p or not p.get("item"):
        return None
    vend = (p.get("itemSeller") or {}).get("webSlug")
    return registro(p["item"], "articulo", vend)


def leer_vendedor(slug):
    p = datos_pagina(traer(f"{WEB}/user/{slug}"))
    if not p:
        return []
    ciudad = ((p.get("user") or {}).get("location") or {}).get("city")
    anuncios = (p.get("publishedItems") or {}).get("data") or []
    return [x for x in (registro(a, "vendedor", slug, ciudad) for a in anuncios) if x]


SUGERIDAS = set()      # "busquedas relacionadas" vistas en esta pasada


def sugeridas_de(seo):
    """Las portadas que enlaza una portada, puestas en Madrid."""
    out = set()
    bloques = (((seo.get("header") or {}).get("suggestedKeywords") or [])
               + ((seo.get("footer") or {}).get("suggestedKeywords") or [])
               + ((seo.get("footer") or {}).get("suggestedLocationKeywords") or []))
    for b in bloques:
        ruta = (b.get("url") or "").strip("/").split("?")[0]
        partes = ruta.split("/")
        if len(partes) == 2:
            ruta += "/madrid"
        if RE_RUTA.match(ruta) and ruta.endswith("/madrid"):
            out.add(ruta)
    return out


def leer_portada(ruta):
    p = datos_pagina(traer(f"{WEB}/{ruta}"))
    if not p:
        return []
    seo = p.get("seoLandingData") or {}
    SUGERIDAS.update(sugeridas_de(seo))
    anuncios = seo.get("items") or []
    return [x for x in (registro(a, "portada") for a in anuncios) if x]


def candidatas(sugeridas, conocidas):
    """Sugeridas que suenan a su gusto y que aun no se leen."""
    def palabra(ruta):          # "muebles-deco-y-jardin/aparador-antiguo/madrid" -> "aparador-antiguo"
        partes = ruta.split("/")
        return partes[1] if len(partes) > 1 else ruta
    return sorted(s for s in sugeridas if s not in conocidas
                  and RE_SUGERIDA_SI.search(palabra(s)) and not RE_SUGERIDA_NO.search(palabra(s)))


def descubrir(tope=15):
    """
    Prueba las busquedas relacionadas que dejo la ultima pasada y guarda las
    que existen en DESCUBIERTAS. Como mucho `tope` peticiones, a 3 s.
    """
    try:
        datos = json.load(open(ARCHIVO, encoding="utf-8"))
    except (OSError, ValueError):
        print("  Primero haz una pasada normal: wallapop.py")
        return []
    ya = descubiertas()
    pendientes = candidatas(datos.get("sugeridas") or [], set(PORTADAS) | set(ya)
                            | set(datos.get("sugeridas_vacias") or []))[:tope]
    print(f"\n=== Wallapop · probando {len(pendientes)} portadas sugeridas ===")
    nuevas, vacias = [], list(datos.get("sugeridas_vacias") or [])
    for ruta in pendientes:
        p = datos_pagina(traer(f"{WEB}/{ruta}"))
        n = len(((p or {}).get("seoLandingData") or {}).get("items") or [])
        print(f"  {n:3d}  {ruta}")
        (nuevas if n >= 20 else vacias).append(ruta)
    if nuevas:
        with open(DESCUBIERTAS, "w", encoding="utf-8") as f:
            json.dump(ya + nuevas, f, ensure_ascii=False, indent=1)
    datos["sugeridas_vacias"] = vacias
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False)
    print(f"  {len(nuevas)} portadas nuevas; entran solas en la proxima pasada")
    return nuevas


def comparar(nuevos, previos, vendedores_vigilados):
    """
    Marca en cada anuncio lo que cambio desde la pasada anterior y devuelve la
    lista de cambios para el resumen. `previos` es {url: registro}.
    Un vendedor que se mira por primera vez no genera "nuevos": todo seria nuevo.
    """
    cambios = []
    ya_vigilados = {p.get("vendedor") for p in previos.values() if p.get("via") == "vendedor"}
    for l in nuevos:
        antes = previos.get(l["url"])
        l["primera_vez"] = (antes or {}).get("primera_vez", l["visto"])
        avisos = []
        if antes:
            pa = antes.get("salida")
            if pa and l["salida"] < pa:
                # puntuar.py lo convierte en "BAJO DE PRECIO" y sube la oportunidad
                l["precio_anterior"] = pa
                cambios.append(("baja", l, f"{pa:.0f} -> {l['salida']:.0f} EUR"))
            elif antes.get("precio_anterior") and l["salida"] == pa:
                l["precio_anterior"] = antes["precio_anterior"]  # la rebaja sigue siendo noticia
            if l["reservado"] and not antes.get("reservado"):
                cambios.append(("reservado", l, ""))
            if l["vendido"] and not antes.get("vendido"):
                cambios.append(("vendido", l, ""))
        elif (l.get("via") == "vendedor" and l.get("vendedor") in vendedores_vigilados
              and l.get("vendedor") in ya_vigilados):
            l["nuevo_de_vendedor"] = True
            cambios.append(("nuevo", l, l["vendedor"]))
        if l["reservado"]:
            avisos.append("RESERVADO en Wallapop")
        if l["vendido"]:
            avisos.append("VENDIDO en Wallapop")
        if l.get("nuevo_de_vendedor"):
            avisos.append(f"anuncio nuevo de {l['vendedor']}, vendedor que vigilas")
        l["avisos_fuente"] = avisos
    return cambios


def desaparecidos(sin_ficha, previos):
    """Piezas guardadas que estaban y ya no responden: borradas o vendidas."""
    out = []
    for slug in sin_ficha:
        url = f"{WEB}/item/{slug}"
        if url in previos and not previos[url].get("vendido"):
            out.append(previos[url])
    return out


def cargar_previos():
    if not os.path.exists(ARCHIVO):
        return {}
    try:
        datos = json.load(open(ARCHIVO, encoding="utf-8"))
    except ValueError:
        return {}
    return {l["url"]: l for l in datos.get("lotes", [])}


def rastrear():
    articulos, vendedores, portadas = listas()
    trabajo = ([("articulo", s) for s in articulos] + [("vendedor", s) for s in vendedores]
               + [("portada", r) for r in portadas])
    if len(trabajo) > TOPE_PAGINAS:
        print(f"  WALLAPOP: {len(trabajo)} paginas pedidas, se leen las {TOPE_PAGINAS} primeras")
        trabajo = trabajo[:TOPE_PAGINAS]
    print(f"\n=== Wallapop · {len(trabajo)} paginas (fichas, perfiles y portadas) ===")
    por_url, sin_ficha = {}, []
    for via, cual in trabajo:
        # ParadaTotal (403) sube hasta __main__: no se guarda una pasada a medias
        if via == "articulo":
            r = leer_articulo(cual)
            trozo = [r] if r else []
            if not r:
                sin_ficha.append(cual)
        elif via == "vendedor":
            trozo = leer_vendedor(cual)
        else:
            trozo = leer_portada(cual)
        for l in trozo:
            # lo guardado a mano y lo vigilado manda sobre la portada
            if l["url"] not in por_url or via != "portada":
                por_url[l["url"]] = l
        print(f"  {len(trozo):3d}  {via}: {cual}")
    # Lo que llega de perfiles y portadas pasa el mismo tope que el resto de
    # fuentes. Las piezas guardadas a mano entran siempre.
    leidos = [l for l in por_url.values()
              if l["via"] == "articulo" or 5 <= l["salida"] <= TOPE_EUR]
    return leidos, sin_ficha, vendedores


def guardar(lotes, cambios, perdidos):
    os.makedirs(DIR_DATOS, exist_ok=True)
    datos = {
        "obtenido": ahora(),
        "lotes": lotes,
        "cambios": [{"tipo": t, "url": l["url"], "titulo": l["titulo"], "detalle": d}
                    for t, l, d in cambios],
        "desaparecidos": [{"url": l["url"], "titulo": l["titulo"]} for l in perdidos],
        "sugeridas": sorted(SUGERIDAS),
        "sugeridas_vacias": previas_vacias(),
    }
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False)
    return ARCHIVO


def previas_vacias():
    """Las sugeridas que ya se probaron sin exito no se vuelven a probar."""
    try:
        return json.load(open(ARCHIVO, encoding="utf-8")).get("sugeridas_vacias") or []
    except (OSError, ValueError):
        return []


def cargar():
    """Para vista.py: los anuncios vivos de la ultima pasada (sin los vendidos)."""
    if not os.path.exists(ARCHIVO):
        return [], "sin datos de Wallapop todavia"
    datos = json.load(open(ARCHIVO, encoding="utf-8"))
    vivos = [l for l in datos.get("lotes", []) if not l.get("vendido")]
    t = datetime.fromisoformat(datos["obtenido"])
    horas = (datetime.now(timezone.utc) - t).total_seconds() / 3600
    return vivos, f"Wallapop de hace {horas:.0f} h"


def resumen(cambios, perdidos):
    nombres = {"baja": "BAJA DE PRECIO", "reservado": "RESERVADO", "vendido": "VENDIDO",
               "nuevo": "NUEVO de vendedor vigilado"}
    lineas = []
    for t, l, d in cambios:
        lineas.append(f"  {nombres[t]:28s} {l['titulo'][:60]}  {d}\n      {l['url']}")
    for l in perdidos:
        lineas.append(f"  {'YA NO ESTA (borrado o vendido)':28s} {l['titulo'][:60]}\n      {l['url']}")
    return "\n".join(lineas) if lineas else "  sin cambios desde la pasada anterior"


if __name__ == "__main__":
    if "--descubrir" in sys.argv:
        try:
            descubrir()
        except ParadaTotal as e:
            print(f"\n!! PARADA TOTAL en Wallapop: {e}")
        sys.exit()
    previos = cargar_previos()
    try:
        lotes, sin_ficha, vendedores = rastrear()
    except ParadaTotal as e:
        print(f"\n!! PARADA TOTAL en Wallapop: {e}\n   No reintentes en bucle. "
              "Se conserva la pasada anterior.")
        sys.exit(1)
    if lotes:
        cambios = comparar(lotes, previos, set(vendedores))
        perdidos = desaparecidos(sin_ficha, previos)
        print(f"  TOTAL Wallapop: {len(lotes)} anuncios")
        print("\nCambios:\n" + resumen(cambios, perdidos))
        print("guardado en", guardar(lotes, cambios, perdidos))
