feat(whatsapp): sessão e mensagens (stub) (#36)

Contexto
- Implementa o fluxo de sessão do WhatsApp (stub) e envio de mensagens para destravar o desenvolvimento do frontend com contrato de API/WS estável.

Principais mudanças
- WS: novo consumidor `ws/whatsapp/` emitindo `session_status`, `qrcode`, `message_status`, `message_received`.
- Stub: `integrations/whatsapp_stub.py` com máquina de estados e modo rápido via `WHATSAPP_STUB_FAST=1`.
- Endpoints REST:
  - POST `/api/v1/whatsapp/session/start` → 202 { status }
  - GET `/api/v1/whatsapp/session/status` → 200 { status }
  - DELETE `/api/v1/whatsapp/session` → 204
  - POST `/api/v1/whatsapp/messages` → 202 { message_id }
- Permissão: `core.manage_config_whatsapp` exigida para operações de sessão/mensagens.
- Config/Infra: `docker-compose` com serviço `newman` e `ALLOWED_HOSTS` incluindo `web`.
- Postman: novas pastas “07 - WhatsApp Sessão”, “08 - WhatsApp Mensagens” e “09 - WhatsApp Cleanup”.
- Testes: 
  - Django: `core/tests/test_whatsapp_session.py` (start/status + envio 202)
  - Newman (Docker): sessão e envio OK contra `web:8000`.

WebSocket
- URL: `ws://localhost:8001/ws/whatsapp/?token=<ACCESS_TOKEN>`
- Eventos: `session_status`, `qrcode`, `message_status`, `message_received`.

Como testar
1) Subir serviços: `docker compose up -d web`
2) Criar admin (se necessário): `docker compose exec -T web python -c "... create/update admin ..."`
3) Django tests: `docker compose exec web python manage.py test core.tests.test_whatsapp_session -v 2`
4) Newman (Docker): `docker compose run --rm newman`

Variáveis relevantes
- `WHATSAPP_STUB_FAST=1` (dev/CI) para transições imediatas.

Notas
- O stub não realiza integração externa; contrato REST/WS foi pensado para ser mantido quando o driver real for plugado.

Checklist
- [x] Endpoints REST protegidos por permissão
- [x] Eventos WS padronizados
- [x] Postman/NeWman atualizados
- [x] Teste Django passando
- [x] README atualizado


