# -*- coding: utf-8 -*-
"""
Sube la pagina a Cloudflare Pages, detras de Cloudflare Access.

Caxi-Vaxi no es publica: la direccion (caxi-vaxi.pages.dev) esta protegida
por Cloudflare Access y solo entran los correos de la lista (Diego y su
pareja). Se entra con un codigo de 6 digitos que llega por email.

Lo que hace:
  1. Copia datos/vista.html a datos/sitio/index.html, con una cabecera que
     prohibe indexar y otra que no deja que nadie la meta en un iframe.
  2. La sube con wrangler, la herramienta oficial de Cloudflare.

La sesion de wrangler vive en tu Mac (npx wrangler login), nunca en el repo.
Si la proteccion de Access no esta puesta, NO sube nada.

Uso:
    .venv/bin/python publicar.py            regenera la vista y la sube
    .venv/bin/python publicar.py --solo     sube la vista que ya hay
"""
import os
import shutil
import subprocess
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scraper import DIR_DATOS

PROYECTO = "caxi-vaxi"
DOMINIO = f"https://{PROYECTO}.pages.dev"
SITIO = os.path.join(DIR_DATOS, "sitio")

CABECERAS = """/*
  X-Robots-Tag: noindex, nofollow
  X-Frame-Options: DENY
  Referrer-Policy: no-referrer
  Cache-Control: no-cache
"""


def protegida():
    """
    Comprueba que el dominio pide inicio de sesion de Access antes de subir.
    Una peticion sin sesion tiene que acabar en el login de Cloudflare Access
    (cloudflareaccess.com), nunca en la pagina.
    """
    req = urllib.request.Request(DOMINIO, method="GET", headers={"User-Agent": "caxi-vaxi-publicar"})

    class SinRedireccion(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    try:
        r = urllib.request.build_opener(SinRedireccion).open(req, timeout=20)
        return False if r.status == 200 else None
    except urllib.error.HTTPError as e:
        destino = e.headers.get("Location", "")
        return e.code in (302, 303) and "cloudflareaccess.com" in destino
    except OSError:
        return None   # todavia no existe o sin red: no hay nada expuesto


def preparar():
    os.makedirs(SITIO, exist_ok=True)
    shutil.copyfile(os.path.join(DIR_DATOS, "vista.html"), os.path.join(SITIO, "index.html"))
    with open(os.path.join(SITIO, "_headers"), "w", encoding="utf-8") as f:
        f.write(CABECERAS)


def subir():
    cmd = ["npx", "--yes", "wrangler@4", "pages", "deploy", SITIO,
           "--project-name", PROYECTO, "--branch", "main", "--commit-dirty=true"]
    return subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__))).returncode


if __name__ == "__main__":
    if "--solo" not in sys.argv:
        import vista
        vista.construir()
    # Solo se sube si la direccion ya pide el login de Access. Sin eso, ni la
    # primera vez: la pagina quedaria abierta a cualquiera con el enlace.
    if protegida() is not True:
        print("!! La direccion no esta protegida por Cloudflare Access. No se sube nada.\n"
              "   Revisa Cloudflare Zero Trust > Access > Applications.")
        sys.exit(1)
    preparar()
    sys.exit(subir())
