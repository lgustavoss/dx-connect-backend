Sistema de Notificações em Tempo Real (WS)

Problema: Entrega de mensagens do WhatsApp Web ao frontend em tempo real.

Integrações:
- Relacionada ao épico #10 e à base de WebSocket (#32 / #5).

Especificação técnica:
- Protocolo de eventos WebSocket
  - message_received
  - message_sent
  - chat_assigned / chat_transferred
  - typing_start / typing_stop
  - session_status (online/offline/reconnecting)
- Payload padrão (v1):
```json
{
  "event": "message_received",
  "data": {
    "from": "5511999999999",
    "message": "Texto",
    "message_id": "abc123",
    "timestamp": "2024-01-01T10:00:00Z",
    "media_url": null,
    "media_type": null
  },
  "version": "v1"
}
```
- Versionamento de eventos: incluir campo "version" com valor "v1".
- Autorização por role nos canais: atendente recebe eventos apenas dos chats sob sua responsabilidade; supervisor por departamento; gerente global.

Critérios de aceitação:
- [ ] Documentação do protocolo publicada
- [ ] Eventos publicados nos pontos de integração (#44/#45)
- [ ] Teste de conexão e ping/pong em ambiente de produção


