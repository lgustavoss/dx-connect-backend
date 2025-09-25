Contratos e Guidelines adicionados:
- docs/api/contracts.md
- docs/api/errors.md
- docs/api/guidelines.md

Dependências:
- Depende de #36 (Config WhatsApp)

Exemplo de schema (MessageReceiveSchema):
```json
{
  "message_id": "abc123",
  "from_number": "5511999999999",
  "content": "Olá",
  "message_type": "text",
  "timestamp": "2024-01-01T10:00:00Z",
  "media_url": null,
  "media_type": null
}
```


