# -*- coding: utf-8 -*-
"""
Enlaces de busqueda listos para los sitios que se consultan A MANO.

Lo que se puede rastrear respetando cada fuente ya tiene su propio modulo: las
cinco casas de Madrid (scraper.py), las tiendas Shopify, Pamono y 1stDibs
(tiendas.py), y por sus APIs oficiales Etsy (etsy.py) y eBay (ebay.py).
Wallapop se lee solo por fichas /item/ y perfiles permitidos (wallapop.py).

Lo que NO se puede rastrear de forma limpia se busca a mano, y este modulo
genera los enlaces con la consulta y el tope ya puestos (comprobado 2026-10-01):

  CATAWIKI       Akamai devuelve 403 a todo lo automatico, robots.txt incluido.
  MERCADO LIBRE  API y web tras un muro de cuenta; su robots.txt bloquea a los
                 bots de IA con Disallow: /. Entrar logueado seria raspar bajo
                 el contrato de usuario, justo lo que la via legal evita.

La parte tediosa (cruzar artistas y palabras con cada sitio) se deja lista en
datos/plan_busqueda.md. Aqui tambien se ofrecen enlaces de Etsy y Wallapop como
atajo manual, aunque ambos ya entren por su rastreador.
"""
import urllib.parse

import perfil

# ---------------------------------------------------------------------------
PALABRAS_WALLAPOP = [
    "mixed media", "patina", "monumental", "art deco", "conciso", "macizo",
    "pesado", "extrano", "tribal", "oriundo", "art nouveau", "maya", "mistico",
    "espiritual", "oculto", "arte povera", "lounge", "puffy", "papiro",
    "plexiglas", "oleo en plexiglas", "crayones al oleo", "glamour", "glamurosa",
    "mesa de espejos", "mesa rustica", "mesa ceramica", "decadente",
    "eclesiastico", "medieval", "middle ages", "dark ages", "racionalista",
    "posmoderna", "40s", "50s", "60s", "70s", "80s", "90s",
    "brutalist", "space-age", "mid-century", "finnish art nouveau",
]

# Los materiales de tu lista NO funcionan solos: "hierro" en Wallapop devuelve
# verjas y herramientas. Son modificadores. Se cruzan con lo que buscas.
MATERIALES = ["hierro", "bronce", "acero", "marmol", "piedra", "ceramica",
              "plexiglas", "papiro"]
OBJETOS = ["escultura", "busto", "figura", "lampara", "mesa", "jarron"]


def cruces_material():
    """La combinatoria util: material x objeto. 48 busquedas que valen algo."""
    out = []
    for o in OBJETOS:
        for mat in MATERIALES:
            out.append(f"{o} {mat}")
    return out

# Las que de verdad encajan con lo que dijo que busca ahora (escultura y bustos,
# mueble de diseno, gran formato). Son las que yo pondria primero.
PRIORITARIAS = [
    "escultura bronce", "busto bronce", "busto marmol", "escultura hierro",
    "escultura marmol", "monumental", "arte povera", "brutalista",
    "mesa de espejos", "art deco", "racionalista", "posmoderna",
    "oleo gran formato", "arte naif", "arte ingenuo", "caricatura original",
    "teca danes", "mueble nordico anos 60", "palisandro anos 60",
]

SITIOS = {
    "catawiki": {
        "nombre": "Catawiki",
        "url": "https://www.catawiki.com/es/s?q={q}",
        "nota": "Akamai bloquea toda lectura automatica (403 hasta en robots.txt). "
                "Buscar a mano y usar 'Guardar busqueda' para recibir alertas. "
                "OJO con la seccion de arte: hay obra generada por IA vendida como pintura.",
    },
    "wallapop": {
        "nombre": "Wallapop",
        "url": "https://es.wallapop.com/app/search?keywords={q}&latitude=40.4168&longitude=-3.7038",
        "nota": "Madrid. Precio fijo y negociable, recogida en mano. Rastreador propio en wallapop.py.",
    },
    "etsy": {
        "nombre": "Etsy",
        "url": "https://www.etsy.com/es/search?q={q}",
        "nota": "Ojo al envio desde EE.UU. y a la aduana. Mucho reproduccion moderna.",
    },
    "ml_ve": {
        "nombre": "Mercado Libre Venezuela",
        "url": "https://listado.mercadolibre.com.ve/{slug}",
        "nota": "Donde de verdad estan tus venezolanos. Necesita cuenta para ver.",
    },
    "ml_mx": {
        "nombre": "Mercado Libre Mexico",
        "url": "https://listado.mercadolibre.com.mx/{slug}",
        "nota": "Segundo mercado de arte latinoamericano.",
    },
}


def _slug(texto):
    s = texto.lower().replace(" ", "-")
    return urllib.parse.quote(s, safe="-")


def enlaces(consulta, sitios=None):
    """Devuelve [(nombre_sitio, url)] para una consulta."""
    out = []
    for clave in (sitios or SITIOS):
        s = SITIOS[clave]
        if "{slug}" in s["url"]:
            out.append((s["nombre"], s["url"].format(slug=_slug(consulta))))
        else:
            out.append((s["nombre"], s["url"].format(q=urllib.parse.quote_plus(consulta))))
    return out


def plan_de_busqueda(incluir_todas=False):
    """
    La combinatoria que a mano no se hace. Artistas venezolanos en Mercado Libre,
    y las palabras de Wallapop en Wallapop y Etsy.
    """
    bloques = []

    bloques.append(("ARTISTAS VENEZOLANOS — Mercado Libre",
                    [(a, enlaces(a, ["ml_ve", "ml_mx"])) for a in perfil.ARTISTAS_VENEZOLANOS]))

    bloques.append(("ARTISTAS QUE SI BAJAN A TU RANGO — todos los sitios",
                    [(a, enlaces(a)) for a in perfil.ARTISTAS_ALCANZABLES]))

    palabras = PALABRAS_WALLAPOP if incluir_todas else PRIORITARIAS
    bloques.append(("PALABRAS CLAVE — Catawiki, Wallapop y Etsy",
                    [(p, enlaces(p, ["catawiki", "wallapop", "etsy"])) for p in palabras]))

    if incluir_todas:
        bloques.append(("MATERIAL x OBJETO — Wallapop (los materiales solos no sirven)",
                        [(c, enlaces(c, ["wallapop"])) for c in cruces_material()]))

    return bloques


def markdown(incluir_todas=False):
    out = ["# Plan de busqueda manual", "",
           "Catawiki y Mercado Libre no se pueden rastrear limpio, asi que se buscan a mano.",
           "La herramienta hace la parte tediosa: la combinatoria.", ""]
    for titulo, filas in plan_de_busqueda(incluir_todas):
        out.append(f"## {titulo}")
        out.append("")
        for consulta, links in filas:
            trozos = " · ".join(f"[{n}]({u})" for n, u in links)
            out.append(f"- **{consulta}** — {trozos}")
        out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    import sys
    todas = "--todas" in sys.argv
    texto = markdown(todas)
    with open("datos/plan_busqueda.md", "w", encoding="utf-8") as f:
        f.write(texto)
    n = sum(len(f) for _, f in plan_de_busqueda(todas))
    print(f"datos/plan_busqueda.md  —  {n} busquedas preparadas")
