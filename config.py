# -*- coding: utf-8 -*-
"""
Configuracion local. Copia este fichero a config_local.py y pon ahi tu correo.
config_local.py esta en .gitignore: no se publica.

El correo va en el User-Agent a proposito. La investigacion legal concluyo que
identificarse con un contacto real convierte "bot sospechoso" en "persona con un
script", y es lo que te salva de un bloqueo por IP.

Ademas, en config_local.py (todas opcionales):
    ETSY_KEYSTRING, ETSY_SHARED_SECRET     etsy.py
    EBAY_CLIENT_ID, EBAY_CLIENT_SECRET     ebay.py (App ID y Cert ID de produccion)
    WALLAPOP_ARTICULOS  = ["slug-o-url", ...]   piezas guardadas
    WALLAPOP_VENDEDORES = ["slug-o-url", ...]   vendedores vigilados
    WALLAPOP_PORTADAS   = ["muebles-deco-y-jardin/aparador-vintage/madrid", ...]
"""
CONTACTO = "pon-tu-correo@ejemplo.com"

try:
    from config_local import CONTACTO  # noqa: F401,F811
except ImportError:
    pass

UA = f"CazaLotes/1.0 (uso personal, no comercial; contacto: {CONTACTO})"
