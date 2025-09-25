# WhatsApp: Recebimento de Mensagens – Especificação

Estrutura de evento (WS):
```json
{
  "event": "message_received",
  "data": {
    "from": "5511999999999",
    "message": "Texto da mensagem",
    "message_id": "abc123",
    "timestamp": "2024-01-01T10:00:00Z",
    "media_url": null,
    "media_type": null
  },
  "version": "v1"
}
```

Requisitos:
- Persistir payload bruto + versão do protocolo
- Latência alvo < 5s (logar tempo entre captura e publicação WS)
- Auth WS por role (atendente só recebe do que lhe pertence)
