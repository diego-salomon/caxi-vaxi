# eBay Browse API: getting the keys

Caxi-Vaxi reads eBay through the Browse API with an application token (no user
sign-in). Two values go in `config_local.py`, which is never committed:

```python
EBAY_CLIENT_ID = "..."       # App ID (Client ID), production keyset
EBAY_CLIENT_SECRET = "..."   # Cert ID (Client Secret)
```

## Steps

1. Create a developer account at [developer.ebay.com](https://developer.ebay.com)
   (individual account is enough) and confirm the email.
2. Under your name, open **Application Keys** and, in the **Production** column,
   create a keyset.
3. **Marketplace Account Deletion exemption.** eBay keeps a production keyset
   disabled until this is resolved. Next to the keyset, open **Notifications** →
   **Marketplace Account Deletion**, turn on **Exempted from Marketplace Account
   Deletion**, and choose the reason *"I do not persist eBay data"*. This is true
   here: `ebay.py` stores only the listing (title, price, image URL, item link),
   never the seller, and overwrites its file on every run.
4. Copy the **App ID** and **Cert ID** from the Production row into
   `config_local.py`.

The application token is cached in `datos/ebay_token.json` (gitignored) and
reused until it is close to expiring.
