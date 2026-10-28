# -*- coding: utf-8 -*-
"""
Configuracion de las casas. Las comisiones se leyeron una a una en sus
condiciones publicadas el 2026-09-30. Cambian: reverificar antes de pujar fuerte.

Las cinco primeras corren el MISMO CMS (Labelgrup), con las mismas rutas.
Por eso un solo scraper las cubre.
"""

CASAS = {
    "salaretiro": {
        "nombre": "Sala Retiro",
        "base": "https://www.salaretiro.com",
        "comision": 0.23,          # 23 % IVA incluido
        "comision_nota": "23 % IVA incluido, en todas sus subastas",
        "iva_sobre_comision": False,
        "almacenaje_dia": 6.0,     # EUR/dia + IVA pasados 10 dias habiles
        "dias_retirada": 10,
        "direccion": "Avenida Menendez Pelayo 3 y 5, 28009 Madrid",
        "listados": ["/es/presenciales/", "/es/venta-directa/"],
        "busqueda": "/es/busqueda?texto={q}",
        "prioridad": 1,            # mejor encaje de precio: 75 % de salidas en 50-200 EUR
    },
    "duran": {
        "nombre": "Duran Arte y Subastas",
        "base": "https://www.duran-subastas.com",
        "comision": 0.23,
        "comision_nota": "23 % IVA incluido; en Compra Ahora el precio ya lo lleva dentro",
        "iva_sobre_comision": False,
        "almacenaje_dia": 6.0,     # muebles, en Camino de Hormigueras 160
        "dias_retirada": 20,
        "direccion": "Goya 19 (sala) / Camino de Hormigueras 160 (muebles)",
        "listados": ["/es/subastas-muebles", "/es/subasta/tienda-online_7500-001"],
        "busqueda": "/es/busqueda?texto={q}",
        "prioridad": 2,
        "nota": "Los lotes no vendidos pasan AUTOMATICAMENTE a venta directa. "
                "Su categoria VINTAGE es moda, no mueble.",
    },
    "segre": {
        "nombre": "Subastas Segre",
        "base": "https://www.subastassegre.es",
        "comision": 0.18,
        "comision_nota": "18 % + IVA sobre la comision = 21,78 % efectivo. La mas barata",
        "iva_sobre_comision": True,
        "almacenaje_dia": None,
        "dias_retirada": None,
        "direccion": "Segre 18, 28002 Madrid",
        "listados": ["/es/subastas"],
        "busqueda": "/es/subastas?description={q}&historic=1",
        "prioridad": 1,
        "nota": "REGLA DEL 40 %: los lotes no vendidos se relanzan con la salida un 40 % "
                "mas baja si el vendedor no retira en 3 meses ni pacta precio. "
                "Es la palanca de descuento mas clara del mercado madrileno.",
        "relanza_40": True,
    },
    "ansorena": {
        "nombre": "Ansorena",
        "base": "https://www.ansorena.com",
        "comision": 0.25,          # 20,66 % + IVA en lotes <= 1000 EUR
        "comision_nota": "25 % en remates <= 1.000 EUR (20,66 % + IVA); 23 % por encima",
        "iva_sobre_comision": False,
        "almacenaje_dia": None,
        "dias_retirada": 15,
        "direccion": "Alcala 52, 28014 Madrid",
        "listados": ["/es/subasta-actual"],
        "busqueda": "/es/busqueda?texto={q}",
        "prioridad": 3,
        "nota": "La mas cara justo en la franja de Diego, pero es la que tiene mejor genero. "
                "No tiene canal de invendidos: el seguro solo cubre 15 dias tras la subasta.",
    },
    "alcala": {
        "nombre": "Alcala Subastas",
        "base": "https://www.alcalasubastas.es",
        "comision": 0.242,
        "comision_nota": "24,2 % IVA incluido (+1,5 % si pagas con American Express)",
        "iva_sobre_comision": False,
        "almacenaje_dia": 2.0,
        "dias_retirada": 7,
        "direccion": "Nunez de Balboa 9, Madrid",
        "listados": ["/es/subastas-presenciales/", "/es/subastas-historicas/"],
        "busqueda": "/es/busqueda?texto={q}",
        "prioridad": 4,
    },
}

# Catawiki NO se rastrea: Akamai devuelve 403 a cualquier lectura automatica,
# robots.txt incluido (comprobado 2026-10-04). Se busca a mano desde los enlaces
# de la pagina, y sus alertas nativas ("Guardar busqueda") hacen el seguimiento.
CATAWIKI = {
    "nombre": "Catawiki",
    "busqueda": "https://www.catawiki.com/es/s?q={q}&max_price={tope}",
    # Condiciones del comprador, septiembre 2026: "9 % del precio de compra mas
    # una cantidad fija (...) suele ser de 3 EUR". Incluye el IVA.
    "comision": 0.09,
    "fijo": 3.0,
    "comision_nota": "9 % + 3 EUR fijos, IVA incluido. Sobre 100 EUR: 112 EUR. "
                     "Mas el envio, que en muebles es tarifa plana orientativa que "
                     "ajustan despues de la compra, con entrega de 2 a 5 semanas.",
    "nota": "La seccion de ARTE esta contaminada con obra generada por IA vendida "
            "como pintura (ver investigacion). Mueble y diseno es donde si funciona.",
}


def coste_catawiki(precio, envio=0.0):
    return precio + precio * CATAWIKI["comision"] + CATAWIKI["fijo"] + envio


# Odalys va aparte: es Shopify, con API JSON publica y sin clave.
ODALYS = {
    "nombre": "Casa de Subastas Odalys",
    "base": "https://odalys.com",
    "api": "https://odalys.com/products.json?limit=250&page={p}",
    "historial": "https://odalys.com/es/pages/auction-history",
    "nota": "1.250+ obras, 453 artistas, arte venezolano. Mediana 1.500 EUR: caro para la "
            "franja de Diego. OJO: el 82 % esta fisicamente en CARACAS, no en Madrid. "
            "Filtrar por ubicacion antes de emocionarse.",
}


def coste_total(remate, casa_id, transporte=0.0, restauracion=0.0):
    """
    Coste real de bolsillo. Sale del manual: nunca mires solo el precio de martillo.
    Devuelve (total, desglose).
    """
    if casa_id not in CASAS:          # tiendas Shopify: precio final, sin prima
        total = remate + transporte + restauracion
        return total, {"martillo": round(remate, 2), "comision": 0.0,
                       "transporte": round(transporte, 2),
                       "restauracion": round(restauracion, 2),
                       "total": round(total, 2),
                       "recargo_pct": round(100 * (total - remate) / remate, 1) if remate else 0}
    c = CASAS[casa_id]
    tasa = c["comision"]
    # Ansorena: 25 % hasta 1.000 EUR de martillo, 23 % por encima
    if casa_id == "ansorena" and remate > 1000:
        tasa = 0.23
    comision = remate * tasa * 1.21 if c["iva_sobre_comision"] else remate * tasa
    total = remate + comision + transporte + restauracion
    return total, {
        "martillo": round(remate, 2),
        "comision": round(comision, 2),
        "transporte": round(transporte, 2),
        "restauracion": round(restauracion, 2),
        "total": round(total, 2),
        "recargo_pct": round(100 * (total - remate) / remate, 1) if remate else 0,
    }


def puja_maxima(valor_mercado, casa_id, transporte=0.0, restauracion=0.0):
    """
    Formula del manual, despejada: cuanto puedo pujar de martillo para no pasarme
    del valor de mercado una vez sumado todo.
    """
    c = CASAS[casa_id]
    factor = 1 + (c["comision"] * 1.21 if c["iva_sobre_comision"] else c["comision"])
    disponible = valor_mercado - transporte - restauracion
    return max(0.0, disponible / factor)
