Contratos e Guidelines adicionados:
- docs/api/contracts.md
- docs/api/errors.md
- docs/api/guidelines.md

Dependências:
- Depende de #36 (Config WhatsApp)

Request/Response (POST /api/whatsapp/send):
```json
{
  "to": "5511999999999",
  "message_type": "text",
  "message": "Olá",
  "media_url": null
}
```


