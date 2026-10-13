# -*- coding: utf-8 -*-
"""
Sube la pagina a Cloudflare Pages, detras de una clave de acceso.

Caxi-Vaxi no es publica. Vive en https://caxi-vaxi.pages.dev, pero todo pasa
por web/functions/_middleware.js: sin la clave solo se ve el formulario de
entrada. La clave es un secreto del proyecto en Cloudflare (CLAVE) y una copia
en config_local.py (CAXIVAXI_CLAVE), nunca en el repo.

Por que una clave y no Cloudflare Access: Access exige guardar una tarjeta. Asi
la cuenta sigue en el plan gratuito y sin metodo de pago: no se le puede cobrar.

Lo que hace:
  1. Copia datos/vista.html a datos/sitio/index.html.
  2. Comprueba que el secreto CLAVE existe en Cloudflare (si no, no sube).
  3. Sube con wrangler desde web/, que lleva la puerta (functions/).
  4. Comprueba que, sin clave, la direccion devuelve el formulario y no la
     pagina. Si no fuese asi, avisa a gritos.

La sesion de wrangler vive en el Llavero del Mac (npx wrangler login), nunca en
el repo.

Uso:
    .venv/bin/python publicar.py            regenera la vista y la sube
    .venv/bin/python publicar.py --solo     sube la vista que ya hay
    .venv/bin/python publicar.py --clave    sube a Cloudflare la clave de config_local.py
    .venv/bin/python publicar.py --enlace   apunta el enlace magico en config_local.py
"""
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)
from scraper import DIR_DATOS

PROYECTO = "caxi-vaxi"
DOMINIO = f"https://{PROYECTO}.pages.dev"
SITIO = os.path.join(DIR_DATOS, "sitio")
WEB = os.path.join(RAIZ, "web")
WRANGLER = ["npx", "--yes", "wrangler@4"]


def wrangler(*args, entrada=None):
    return subprocess.run(WRANGLER + list(args), cwd=WEB, input=entrada,
                          capture_output=True, text=True)


def hay_clave():
    r = wrangler("pages", "secret", "list", "--project-name", PROYECTO)
    return r.returncode == 0 and "CLAVE" in r.stdout


def subir_clave():
    """Pone en Cloudflare la clave de config_local.py, sin mostrarla."""
    import config_local
    clave = getattr(config_local, "CAXIVAXI_CLAVE", "")
    if len(clave) < 12:
        sys.exit("Falta CAXIVAXI_CLAVE (12 caracteres o mas) en config_local.py")
    r = wrangler("pages", "secret", "put", "CLAVE", "--project-name", PROYECTO, entrada=clave + "\n")
    print("clave subida" if r.returncode == 0 else "no se pudo subir la clave:\n" + r.stderr[-400:])
    return r.returncode == 0


def enlace_magico():
    """
    El enlace "no listado": entra sin escribir la clave. Sale de la clave
    (misma cuenta que web/functions/_middleware.js) y se apunta en
    config_local.py como CAXIVAXI_ENLACE. Cambiar la clave lo anula.
    """
    import hashlib
    import hmac
    import config_local
    clave = config_local.CAXIVAXI_CLAVE
    ficha = hmac.new(clave.encode(), b"enlace-v1", hashlib.sha256).hexdigest()[:32]
    url = f"{DOMINIO}/e/{ficha}"
    ruta = os.path.join(RAIZ, "config_local.py")
    texto = open(ruta, encoding="utf-8").read()
    if "CAXIVAXI_ENLACE" not in texto:
        with open(ruta, "a", encoding="utf-8") as f:
            f.write("# Enlace magico: entra sin escribir la clave. Compartelo solo con quien quieras.\n")
            f.write(f'CAXIVAXI_ENLACE = "{url}"\n')
    return url


def cerrada(url=DOMINIO, intentos=8):
    """
    True si, sin cookie, la direccion responde con el formulario (401).
    False solo si devuelve los datos de verdad sin clave. Justo despues de
    subir, Cloudflare tarda unos segundos en propagar: se reintenta.
    """
    import time
    for n in range(intentos):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "caxi-vaxi"}), timeout=30)
            if "const DATOS" in r.read().decode("utf-8", "ignore"):
                return False               # la pagina entera, sin clave: abierta
        except urllib.error.HTTPError as e:
            if e.code == 401 and 'name="clave"' in e.read().decode("utf-8", "ignore"):
                return True
        except OSError:
            pass
        time.sleep(8)
    return None


def preparar():
    os.makedirs(SITIO, exist_ok=True)
    shutil.copyfile(os.path.join(DIR_DATOS, "vista.html"), os.path.join(SITIO, "index.html"))


def subir():
    r = subprocess.run(WRANGLER + ["pages", "deploy", SITIO, "--project-name", PROYECTO,
                                   "--branch", "main", "--commit-dirty=true"], cwd=WEB)
    return r.returncode


if __name__ == "__main__":
    if "--clave" in sys.argv:
        sys.exit(0 if subir_clave() else 1)
    if "--enlace" in sys.argv:
        enlace_magico()
        sys.exit("enlace magico apuntado en config_local.py (CAXIVAXI_ENLACE)")
    if not os.path.exists(os.path.join(WEB, "functions", "_middleware.js")):
        sys.exit("!! Falta web/functions/_middleware.js: sin puerta no se sube nada.")
    if not hay_clave():
        sys.exit("!! El proyecto no tiene la clave CLAVE en Cloudflare. No se sube nada.\n"
                 "   Ponla con: .venv/bin/python publicar.py --clave")
    if "--solo" not in sys.argv:
        import vista
        vista.construir()
    preparar()
    codigo = subir()
    if codigo == 0:
        estado = cerrada()
        if estado is False:
            print("!! ATENCION: la pagina responde SIN clave. Revisa web/functions/_middleware.js.")
            sys.exit(2)
        print("  comprobado: sin clave solo se ve el formulario" if estado else
              "  (no se pudo comprobar la puerta ahora; se revisa en la siguiente pasada)")
    sys.exit(codigo)
