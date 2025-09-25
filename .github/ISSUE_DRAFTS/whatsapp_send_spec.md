# WhatsApp: Envio de Mensagens – Especificação

API HTTP:
POST /api/whatsapp/send
```json
{
  "to": "5511999999999",
  "message": "Texto da mensagem",
  "media_url": null,
  "message_type": "text"
}
```
- message_type: text | image | audio

Requisitos:
- Fila/retentativas para envio
- Evento WS de confirmação: `message_sent` com `message_id` e status
- Validação de payload e permissões
