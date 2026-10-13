import json
import os
import sys
import warnings

warnings.simplefilter("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def pagina(page_props):
    """Una pagina de Wallapop minima: solo el bloque __NEXT_DATA__."""
    datos = json.dumps({"props": {"pageProps": page_props}}, ensure_ascii=False)
    return ('<!doctype html><html><body><div id="__next"></div>'
            f'<script id="__NEXT_DATA__" type="application/json">{datos}</script></body></html>')


# Formas copiadas de las paginas reales del 2026-10-13, con datos inventados.
FICHA = {
    "id": "abc123",
    "title": {"original": "Aparador danés de teca", "translated": None},
    "description": {"original": "Aparador de los años 60 con cuatro cajones.\n\n"
                                "Medidas: 190cm ancho x 42cm fondo x 78cm alto.\n\n"
                                "Space age, minimalista, retro, Art decó, Mid Century, "
                                "escandinavo, nórdico, vintage, Danish", "translated": None},
    "characteristics": "Buen estado · Marrón · Madera",
    "slug": "aparador-danes-de-teca-1000000001",
    "images": [{"id": "x", "urls": {
        "small": "https://cdn.wallapop.com/images/1/a.jpg?pictureSize=W320",
        "medium": "https://cdn.wallapop.com/images/1/a.jpg?pictureSize=W640",
        "big": "https://cdn.wallapop.com/images/1/a.jpg?pictureSize=W800"}}],
    "price": {"cash": {"amount": 450, "currency": "EUR"}, "financed": None},
    "location": {"city": "Madrid", "postalCode": "28001", "countryCode": "ES"},
    "flags": {"reserved": False, "sold": False, "expired": False, "onHold": False},
    "measures": None,
}
VENDEDOR_PAGINA = {
    "user": {"webSlug": "vendedor-1", "location": {"city": "Alcalá de Henares"}},
    "publishedItems": {"meta": {"next": "cursor"}, "data": [
        {"id": "p1", "title": "Silla Thonet", "description": "Silla de 1970. 45 x 50 x 85 cm",
         "slug": "silla-thonet-1000000002", "images": [],
         "price": {"amount": 80, "currency": "EUR"}, "isReserved": True},
        {"id": "p2", "title": "Lámpara de pie", "description": "Funciona",
         "slug": "lampara-de-pie-1000000003", "images": [],
         "price": {"amount": 2500, "currency": "EUR"}, "isReserved": False},
    ]},
}
PORTADA_PAGINA = {
    "seoLandingData": {"items": [
        {"id": 1000000004, "title": "Cómoda vintage", "description": "Cómoda de roble",
         "price": 120, "currency": "EUR", "slugId": "comoda-vintage-1000000004",
         "sold": False, "reserved": False, "seller": {"slug": "otro-vendedor-9"},
         "images": [{"smallUrl": "https://cdn.wallapop.com/images/2/b.jpg?pictureSize=W320"}]},
        {"id": 1000000005, "title": "Regalo", "description": "", "price": 0,
         "currency": "EUR", "slugId": "regalo-1000000005", "sold": False, "reserved": False},
    ]},
}

# Browse API: un itemSummary y la ficha de get_items, con la forma de su OpenAPI
RESUMEN_EBAY = {
    "itemId": "v1|1234567890|0",
    "title": "Aparador vintage de teca años 60",
    "price": {"value": "350.00", "currency": "EUR"},
    "buyingOptions": ["FIXED_PRICE"],
    "condition": "Usado",
    "image": {"imageUrl": "https://i.ebayimg.com/images/g/AbC/s-l225.jpg"},
    "itemWebUrl": "https://www.ebay.es/itm/1234567890?hash=item1&var=0",
    "itemLocation": {"postalCode": "28***", "country": "ES", "city": "Madrid"},
    "seller": {"username": "alguien_real", "feedbackPercentage": "99.5", "feedbackScore": 300},
    "marketingPrice": {"originalPrice": {"value": "420.00", "currency": "EUR"},
                       "discountPercentage": "17"},
}
FICHA_EBAY = {
    "itemId": "v1|1234567890|0",
    "shortDescription": "Aparador en buen estado.",
    "localizedAspects": [
        {"type": "STRING", "name": "Anchura", "value": "160 cm"},
        {"type": "STRING", "name": "Altura", "value": "0,75 m"},
        {"type": "STRING", "name": "Profundidad", "value": "45 cm"},
        {"type": "STRING", "name": "Material", "value": "Teca"},
        {"type": "STRING", "name": "Marca", "value": "Sin marca"},
    ],
}
