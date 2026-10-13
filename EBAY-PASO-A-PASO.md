# eBay: cómo sacar las claves para Caxi-Vaxi

Unos 15 minutos, más la espera de aprobación (hasta un día hábil).
La pestaña de Chrome ya está abierta en la página de registro.

## 1. Crear la cuenta de desarrollador

1. En **developer.ebay.com**, pestaña **Register**.
2. Rellena tus datos y elige cuenta **individual** (Individual, no Business).
3. Acepta el acuerdo de licencia de la API y envía.
4. eBay manda un correo de confirmación. Ábrelo y confirma.
5. La aprobación puede tardar hasta un día hábil. Te llega otro correo cuando esté lista.

## 2. Crear las claves de producción

1. Entra en **developer.ebay.com** con tu usuario.
2. Arriba a la derecha, tu nombre → **Application Keys**.
3. Escribe un nombre para la app, por ejemplo `caxivaxi`.
4. En la columna **Production** (no Sandbox), pulsa **Create a keyset**.

## 3. Exención de notificaciones (obligatoria para que las claves funcionen)

eBay no activa las claves de producción hasta que resuelves esto.

1. En la misma página, junto a tu App ID de **Production**, pulsa **Notifications**.
2. Entra en **Marketplace Account Deletion**.
3. Activa el interruptor **Not persisting eBay data** y pulsa **Confirm**.
4. En **Exemption reason**, elige la opción que diga que **no guardas datos de usuarios de eBay**.
5. Pulsa **Submit**. Tiene que aparecer **Exemption Enabled**.

Esto es verdad para Caxi-Vaxi: `ebay.py` no guarda nada de los vendedores, solo las piezas,
y borra el archivo en cada pasada. eBay advierte que mentir aquí puede costar la cuenta.

## 4. Pegar las claves

1. De la fila **Production** copia dos valores:
   - **App ID (Client ID)**
   - **Cert ID (Client Secret)**
   El Dev ID no hace falta.
2. Abre `config_local.py` (está en esta misma carpeta) y añade al final:

   ```python
   # eBay Browse API (keyset de produccion)
   EBAY_CLIENT_ID = "pega-aqui-el-App-ID"
   EBAY_CLIENT_SECRET = "pega-aqui-el-Cert-ID"
   ```

3. Guarda. Ese archivo no se sube a GitHub.
4. No me pegues las claves en el chat. Dime solo «listo» y yo hago la primera pasada.

## Lo que hago yo después

- `ebay.py --categorias aparador` para acotar por categorías de eBay.es.
- La primera pasada real y la página regenerada.
