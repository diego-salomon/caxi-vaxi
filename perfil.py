# -*- coding: utf-8 -*-
"""
Perfil de gusto de Diego. Esto es lo que convierte el scraper en un filtro personal
en lugar de un buscador. Se edita a mano a medida que Diego marca lotes.

Regla de fondo que sale de toda la investigacion: el titulo del lote NO es de fiar
(es posicionamiento en buscadores, y desde 2026 muchas casas lo generan con IA).
Por eso aqui no buscamos "lo que dice ser", buscamos senales.
"""

# ---------------------------------------------------------------------------
# ARTISTAS QUE BUSCA POR NOMBRE
# ---------------------------------------------------------------------------
# Venezolanos, sobre todo ingenuos. Lista de Diego (Mercado Libre).
# El peso alto es porque un acierto de nombre vale mas que diez de palabra clave.
ARTISTAS_VENEZOLANOS = [
    "Barbaro Rivas", "Pedro Leon Zapata", "Jose Gregorio Camacho",
    "Salvador Valero", "Onofre Frias", "Mateo Manaure", "Feliciano Carvallo",
    "Jacobo Borges", "Jose Cheo Perez", "Antonio Jose Fernandez",
    "El Hombre Del Anillo", "Oswaldo Vigas", "Juan Calzadilla",
    "Alirio Rodriguez", "Emilita Rondon", "Juanita Alvarez", "Rafaela Baroni",
    "Elias Toro Jimenez", "Adonay Duque", "Edgar Sanchez", "Emilio Boggio",
    "Roberto Weil", "Esteban Mendoza", "Felicinda Salazar",
]

# Los que la investigacion confirmo que SI bajan a 50-600 EUR, casi siempre
# como obra grafica o multiple. Es donde de verdad puede comprar.
ARTISTAS_ALCANZABLES = [
    "Jesus Rafael Soto", "Jesus Soto", "Carlos Cruz-Diez", "Cruz Diez",
    "Gego", "Hector Poleo", "Alejandro Otero", "Francisco Narvaez",
    "Manuel Cabre",
]

# Diego dijo "Dali 100% me interesa que este".
# Aviso permanente: ver AVISOS_POR_ARTISTA mas abajo.
ARTISTAS_OTROS = ["Salvador Dali", "Joan Miro", "Pablo Picasso", "Eduardo Chillida"]

ARTISTAS = ARTISTAS_VENEZOLANOS + ARTISTAS_ALCANZABLES + ARTISTAS_OTROS

AVISOS_POR_ARTISTA = {
    "dali": (
        "Dali grafico: su secretario Peter Moore fue condenado en Figueres; se hallaron "
        "10.000 litografias falsas y firmaba hojas en blanco. Las autenticas van de 2.000 a "
        "15.000 GBP. Un 'Dali' de 200 EUR es decoracion. Exige numero de Michler & Lopsinger."
    ),
    "miro": (
        "Miro: la obra grafica NO la certifica el Comite Miro sino la Fundacio Joan Miro de "
        "Barcelona. Abrir expediente cuesta 200 EUR + IVA, mas que el lote."
    ),
    "picasso": (
        "Ojo al encabezado del catalogo: Segre escribe 'AFTER PABLO PICASSO' cuando solo hay "
        "firma en plancha. Diferencia de precio de 3 a 4 veces."
    ),
    "chillida": (
        "Hay obra grafica falsa de Chillida documentada en juzgados de Madrid (sentencia TSJ "
        "2023). Se detectaron por numeracion con tecnica incorrecta."
    ),
}

# ---------------------------------------------------------------------------
# LO QUE LE GUSTA
# ---------------------------------------------------------------------------
# Peso 3 = senal fuerte, 2 = media, 1 = leve.
GUSTA = {
    # Arte ingenuo, su coleccion principal
    "ingenuo": 3, "naif": 3, "naive": 3, "primitivista": 3, "art brut": 2,
    "outsider": 2, "autodidacta": 2, "popular venezolano": 3,

    # Caricatura y dibujo de prensa
    "caricatura": 3, "caricaturista": 3, "humor grafico": 3, "vineta": 2,
    "satira": 2, "ilustracion": 1,

    # Escultura y bustos: lo que busca ahora mismo
    "escultura": 3, "busto": 3, "talla": 2, "figura exenta": 2, "relieve": 1,
    "bronce": 2, "marmol": 2, "hierro": 2, "acero": 2, "piedra": 2, "ceramica": 2,
    "terracota": 2, "alabastro": 2,

    # Escenas mundanas, que es lo que pidio explicitamente
    "escena costumbrista": 3, "costumbrista": 3, "mercado": 2, "taberna": 2,
    "cafe": 2, "calle": 2, "vida cotidiana": 3, "campesino": 2, "pescador": 2,
    "feria": 2, "carnaval": 2, "musicos": 2, "baile": 2,

    # Raro, quirky
    "curiosa": 2, "curioso": 2, "insolito": 3, "extrano": 3, "rareza": 3,
    "singular": 2, "excentrico": 3, "kitsch": 2, "surrealista": 2,
    "fantastico": 2, "onirico": 2,

    # Mueble de diseno, 1950 en adelante
    "diseno": 3, "disenador": 3, "mid century": 3, "midcentury": 3,
    "escandinavo": 3, "nordico": 3, "danes": 3, "teca": 3, "palisandro": 3,
    "vintage": 1, "anos 50": 3, "anos 60": 3, "anos 70": 3, "space age": 3,
    "art deco": 2, "bauhaus": 3, "italiano": 1,  # "racionalista" esta mas abajo con mas peso

    # Marcas de mueble que valen la pena (de la investigacion)
    "wegner": 3, "finn juhl": 3, "fritz hansen": 3, "carl hansen": 3,
    "france & son": 3, "getama": 3, "cassina": 3, "kartell": 3, "artemide": 3,
    "knoll": 3, "gavina": 3, "zanotta": 3, "arflex": 3, "eames": 3,
    "jacobsen": 3, "panton": 3, "saarinen": 3, "paul mccobb": 3,
    "dansk mobelkontrol": 3, "danish furnituremakers": 3,

    # Materiales y acabados de su lista de Wallapop
    "mixta": 1, "tecnica mixta": 1, "patina": 2, "monumental": 3,
    "macizo": 2, "maciza": 2, "tribal": 2, "art nouveau": 2, "plexiglas": 2,
    "papiro": 2, "oriundo": 1, "mistico": 2, "arte povera": 3, "brutalista": 3,
    "posmoderna": 3, "posmoderno": 3, "postmoderno": 3,

    # Decadas. Son tokens cortos: se buscan con limite de palabra (ver puntuar.py).
    # En catalogo espanol casi siempre se escribe "anos 50"; en Wallapop y en
    # vendedores de diseno, "50s". Van las dos formas.
    "40s": 2, "50s": 3, "60s": 3, "70s": 3, "80s": 2, "90s": 1,
    "anos 40": 2, "anos 80": 2, "anos 90": 1,
    "1950": 3, "1960": 3, "1970": 3,

    # Formas inglesas que usan los vendedores de diseno
    "brutalist": 3, "space-age": 3, "spaceage": 3, "mid-century": 3,
    "danish": 3, "teak": 3, "rosewood": 3, "scandinavian": 3,

    # "Finish Art Nouveau" de tu lista: lo leo como art nouveau finlandes
    # (romanticismo nacional). Si querias otra cosa, dimelo.
    "finlandes": 2, "finnish": 2, "jugendstil": 2, "secesion": 2,
    "wiener werkstatte": 3, "vienna secession": 3, "viena": 1,

    # --- EL EJE QUE DIEGO DESCRIBIO: ascetismo con diseno pensado ---
    # Shaker, Barragan, Donald Judd, Christopher Alexander. Lineas simples,
    # material honesto, sin ornamento, humilde pero proyectado.
    "shaker": 3, "minimalista": 3, "minimalist": 3, "ascetico": 3,
    "austero": 2, "sobrio": 2, "lineas puras": 3, "lineas simples": 3,
    "sin ornamento": 3, "esencial": 2, "geometrico": 2, "modular": 3,
    "barragan": 3, "donald judd": 3, "judd": 2, "wabi": 3, "wabi sabi": 3,
    "de stijl": 3, "ulm": 3, "braun": 2, "dieter rams": 3,
    "madera maciza": 3, "roble macizo": 3, "nogal macizo": 3, "pino macizo": 2,
    "artesanal": 2, "hecho a mano": 2, "carpinteria": 2, "ebanisteria": 3,

    # --- DISENADORES extraidos de La Basilica Galeria (Barcelona) ---
    "ico parisi": 4,  # el armario que si le gusta es suyo
    "joe colombo": 3, "manfredo massironi": 3,  # gavina ya esta arriba
    "ludvik volak": 3, "fratelli reguitti": 4,  # su referencia explicita de almacenaje
    "oluce": 3, "kazuhide takahama": 3,
    "harvey guzzini": 3, "guzzini": 2, "formanova": 3, "meurop": 3,
    "maitland-smith": 2, "berrocal": 3, "moscatelli": 3, "raumdesign": 2,
    "bizette-lindet": 3, "moerenhout": 3, "trocme": 2, "urquiola": 3,
    "bentwood": 2, "openwork": 2, "wrought iron": 2, "chrome finish": 2,
    "cromado": 2, "polistireno": 1,

    # === DE SUS FAVORITOS DE WALLAPOP (40 items, 7 listas) ===
    # AVISO DE LECTURA: el bloque de comodas/cajoneras/aparadores de esos
    # favoritos (IKEA Malm, KOPPANG, Maisons du Monde, Luis Philippe, comoda
    # blanca de 30 EUR) NO es gusto: era busqueda activa para el dormitorio.
    # Diego lo confirmo: "las comodas y cajoneras son una mierda, ignoralo".
    # La UNICA excepcion es el armario de Ico Parisi para Fratelli Reguitti.
    # O sea: no quiere "una comoda", quiere almacenaje italiano mid-century.
    # Por eso los negativos de anticuario (luis felipe, marqueteria, tallado)
    # se quedan como estan. Estaban bien.
    # Su palabra: "racionalista" sale 4 veces entre sus favoritos y los
    # vendedores espanoles la usan. Es la mas rentable de todas.
    "racionalista": 3, "racionalistas": 3,

    # FLEXOS: su lista mas grande, 72 items. No teniamos NADA de esto.
    "flexo": 3, "lampara articulada": 3, "lampara de arquitecto": 3,
    "lampara de trabajo": 3, "aplique articulado": 3, "brazo articulado": 3,
    "swing arm": 3, "architect lamp": 3, "task lamp": 3, "desk lamp": 2,
    "jielde": 3, "tolomeo": 3, "markslojd": 3, "portland": 2, "luxo": 3,
    "anglepoise": 3, "naska loris": 3, "fase": 3, "lupela": 3, "gei": 2,
    "lampara de sobremesa": 2, "lampara de pie": 2, "aplique": 2,

    # SILLAS: segunda lista, 70 items.
    "silla": 2, "sillas": 2, "butaca": 2, "sillon": 2, "taburete": 2,
    "banqueta": 2, "silla de despacho": 3, "silla de oficina": 3,
    "enea": 2, "anea": 2, "rejilla": 2, "cane": 2, "contrachapado": 2,

    # Mesas: tercera y cuarta lista.
    "mesa de centro": 2, "mesa de comedor": 2, "mesita": 2, "velador": 2,

    # Disenadores y marcas que YA perseguia el solo
    "gio ponti": 4, "ponti": 2, "truck furniture": 3,
    "carlo hauner": 3, "hauner": 2, "luigi brusotti": 3, "brusotti": 2,
    "pino melis": 3, "simon gavina": 3, "philips": 2, "infraphil": 3,
    "delaunay": 2,

    # Lo raro, que confirmo con creces
    "erotic": 2, "erotico": 2, "feria": 2, "mickey": 2, "atraccion": 2,
    "cojin vintage": 2, "espejo": 2,
    "conciso": 1, "pesado": 1, "decadente": 2, "glamour": 2, "glamurosa": 2,
    "lounge": 2, "puffy": 2, "mesa de espejos": 3, "oculto": 2, "espiritual": 1,
    "maya": 2, "precolombino": 2, "crayones al oleo": 2, "oleo en plexiglas": 3,

    # Registro estetico oscuro/medieval de su lista de Wallapop.
    # OJO: esto es el AMBIENTE, no el tema devocional. Un armario gotico si,
    # una Virgen con el Nino no. Los temas devocionales siguen en negativo abajo.
    "medieval": 2, "middle ages": 2, "dark ages": 2, "gotico": 2,
}

# ---------------------------------------------------------------------------
# LO QUE NO QUIERE
# ---------------------------------------------------------------------------
# Negativo fuerte: descarta el lote salvo que algo muy fuerte lo rescate.
NO_GUSTA_FUERTE = {
    # Religioso, dijo que no le interesa nada
    "religios": -5, "cristo": -5, "crucifi": -5, "virgen": -5, "santo": -4,
    "santa ": -4, "inmaculada": -5, "sagrado corazon": -5, "via crucis": -5,
    "nacimiento": -4, "belen": -4, "piedad": -4, "anunciacion": -5,
    "apostol": -4, "evangelista": -4, "eclesiastic": -4, "liturgic": -4,
    "reliquia": -4, "retablo": -4,
    # Quitadas por ambiguas: "icono" (salta en "icono del diseno"),
    # "caliz" (en "piedra caliza") y "custodia" (en texto corriente).
    "icono religioso": -4, "caliz de plata": -4, "custodia procesional": -4,

    # Mueble de anticuario clasico, dijo que no le interesa nada
    "castellano": -4, "isabelin": -4, "fernandin": -4, "victorian": -4,  # "castellano", no "castellan" (saltaba en Paseo de la Castellana)
    "renacimiento": -4, "renacentista": -4, "barroc": -4, "luis xv": -4,
    # los "neo" del XIX: el limite de palabra no deja que "renacentista"
    # salte dentro de "neorrenacentista", asi que van con nombre propio
    "neorrenacent": -4, "neorenacent": -4, "neogotic": -4, "neobarroc": -4,
    "henri ii": -4, "enrique ii": -4,
    # lo mismo en ingles, para Etsy, 1stDibs y The Oblist
    "renaissance": -4, "baroque": -4, "rococo": -4, "louis xv": -4,
    "gothic revival": -4, "edwardian": -3, "regency": -3,
    "luis xvi": -4, "luis felipe": -4, "imperio": -3, "napoleon iii": -4,
    "alfonsin": -4, "carlos iv": -4, "bargueno": -4, "vitrina ingles": -3,
    "chippendale": -3, "hepplewhite": -3, "reina ana": -3, "estilo ingles": -3,
    "tocinera": -4, "frailero": -4, "arcon": -3,
}

# Negativo suave: resta, no descarta.
NO_GUSTA_SUAVE = {
    "retrato de caballero": -2, "retrato de dama": -2, "retrato anonimo": -2,
    "bodegon": -1, "flores": -1, "marina": -1, "paisaje convencional": -1,
    "porcelana decorativa": -1, "capodimonte": -2, "lladro": -2,
    "cuberteria": -2, "juego de cafe": -2, "mantel": -2, "abanico": -1,
    # Joyeria y relojeria: Diego no los menciono nunca. Fuera del radar.
    "sortija": -6, "pendientes": -6, "collar": -5, "pulsera": -5,
    "broche": -4, "gargantilla": -5, "reloj de pulsera": -6, "brillantes": -4,
    "diamantes": -4, "oro de ley": -4, "plata de ley": -4, "quilates": -5,
    "reloj": -6, "automatico": -3, "cuarzo": -4, "correa de piel": -4,
    "netsuke": -3, "marfilina": -3,

    # === EXCLUSIONES EXPLICITAS DE DIEGO (01/10/2026) ===
    # "no me interesan Boosters, todo lo que son posters, es mas, serigrafias
    #  y cosas asi reproducibles en masa no me gustan para nada"
    "poster": -6, "cartel": -5, "afiche": -5, "lamina": -5, "reproduccion": -5,
    "serigrafia": -6, "litografia": -4, "offset": -6, "giclee": -6,
    "impresion digital": -6, "edicion limitada": -2, "numerada": -1,
    "ejemplares": -2, "tirada": -2, "estampa": -3, "grabado": -2,

    # "no quiero nada de botellas de vino ni joyas en general"
    "vino": -6, "botella": -5, "bodega": -4, "rioja": -5, "champagne": -5,
    "whisky": -5, "licor": -5, "magnum": -4, "anada": -4, "denominacion": -3,
    "joya": -6, "joyeria": -6, "bisuteria": -5, "gemelos": -4, "camafeo": -4,
    # Ornamento dorado y tallado: lo contrario del eje Shaker/Barragan/Judd
    "dorada": -4, "dorado": -3, "pan de oro": -4, "estucad": -4,
    "tallada": -3, "tallado": -3, "capitel": -3, "columna": -2,
    "flores de loto": -4, "marqueteria": -2, "incrustacion": -2,
    "rocalla": -4, "venera": -3, "querubin": -4, "angelote": -4,
}

# ---------------------------------------------------------------------------
# GRAN FORMATO
# ---------------------------------------------------------------------------
# Diego prefiere obra grande. La investigacion dice ademas que el formato grande
# espanta a los compradores por logistica, asi que remata mas barato.
# Su gusto y la ineficiencia del mercado apuntan al mismo sitio.
GRAN_FORMATO_CM = 100          # lado mayor a partir del cual cuenta como grande
BONUS_GRAN_FORMATO = 3
BONUS_MUY_GRANDE = 5           # a partir de 150 cm

# ---------------------------------------------------------------------------
# PRESUPUESTO
# ---------------------------------------------------------------------------
PRECIO_MIN = 30
PRECIO_MAX = 600
PRECIO_MAX_ESTIRANDO = 900     # si la puntuacion es muy alta, avisa igual

# ---------------------------------------------------------------------------
# SENALES DE CATALOGO (jerarquia literal de Duran y Ansorena)
# ---------------------------------------------------------------------------
# Esto no es gusto, es lectura del catalogo. Cuando la casa escribe una de estas
# formulas esta diciendo, en su propio codigo, que NO es del artista.
GRADOS_ATRIBUCION = {
    "atribuido a": "probable, con desacuerdo entre expertos",
    "taller de": "mano desconocida del taller, NO del artista",
    "circulo de": "pintor desconocido siguiendo el estilo, NO del artista",
    "seguidor de": "imitador, NO del artista",
    "segun ": "obra de un imitador copiando",
    "copia de": "copia de una obra celebre",
    "escuela ": "artista de esa escuela, sin identificar",
    "con firma de": "FIRMA DE OTRA MANO, sin conocimiento del artista",
    "after ": "solo firma en plancha (uso de Segre)",
    "estilo ": "reproduccion (equivalente de 'segun' en mueble)",
    "al gusto de": "reproduccion",
    "de epoca posterior": "reproduccion",
}

# Lo mismo en ingles, para Etsy. "after " NO entra: en un anuncio en ingles sale
# en cualquier frase ("after cleaning") y marcaba 96 anuncios por error.
GRADOS_ATRIBUCION_EN = {
    "in the style of": "'al estilo de': NO es del disenador",
    "style of ": "'al estilo de': NO es del disenador",
    "inspired by": "inspirado en: NO es del disenador",
    "attributed to": "atribuido: sin certeza",
    "manner of": "a la manera de: imitacion",
    "circle of": "circulo de: NO es del artista",
    "school of": "escuela de: artista sin identificar",
    "replica": "replica declarada",
    "reproduction": "reproduccion declarada",
}

# Firma: la diferencia que multiplica el precio por 3 o 4.
FIRMA_BUENA = ["firmado a lapiz", "firmada a lapiz", "justificada a lapiz",
               "firmado abajo", "firmada abajo", "firmado y numerado a lapiz"]
FIRMA_MALA = ["firmado en plancha", "firmada en plancha", "en la plancha",
              "firmado en la piedra", "signed in the plate", "sobre passepartout",
              "sobre paspartu"]
