# 📋 Lista Completa de Endpoints - DX Connect Backend

**Base URL**: `http://localhost:8001`

**Atualizado em**: 12 de Outubro de 2025

---

## 📑 Índice Rápido

- [Autenticação](#autenticação) (3 endpoints)
- [Clientes](#clientes) (16 endpoints)
- [Contatos](#contatos) (6 endpoints)
- [Documentos](#documentos) (8 endpoints)
- [WhatsApp](#whatsapp) (19 endpoints)
- [Chats](#chats) (6 endpoints)
- [Atendimento](#atendimento) (15 endpoints)
- [Notificações e Presença](#notificações-e-presença) (7 endpoints)
- [Configurações](#configurações) (11 endpoints)
- [Integrações](#integrações) (1 endpoint)
- [Permissões](#permissões) (4 endpoints)
- [WebSocket](#websocket) (2 conexões)
- [Documentação](#documentação) (3 endpoints)

**Total: 100 endpoints**

---

## 🔐 Autenticação

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `POST` | `/api/v1/auth/token/` | Obter token JWT | ❌ |
| `POST` | `/api/v1/auth/refresh/` | Renovar token | ❌ |
| `GET` | `/api/v1/me/` | Dados do usuário autenticado | ✅ |

---

## 👥 Clientes

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/api/v1/clientes/` | Listar clientes | ✅ |
| `POST` | `/api/v1/clientes/` | Criar cliente | ✅ |
| `GET` | `/api/v1/clientes/{id}/` | Detalhar cliente | ✅ |
| `PUT` | `/api/v1/clientes/{id}/` | Atualizar cliente (completo) | ✅ |
| `PATCH` | `/api/v1/clientes/{id}/` | Atualizar cliente (parcial) | ✅ |
| `DELETE` | `/api/v1/clientes/{id}/` | Deletar cliente | ✅ |
| `GET` | `/api/v1/clientes/search/` | Buscar clientes | ✅ |
| `GET` | `/api/v1/clientes/status/{status}/` | Listar por status | ✅ |
| `PATCH` | `/api/v1/clientes/{id}/status/` | Alterar status | ✅ |
| `GET` | `/api/v1/clientes/stats/` | Estatísticas | ✅ |
| `GET` | `/api/v1/grupos-empresa/` | Listar grupos | ✅ |
| `POST` | `/api/v1/grupos-empresa/` | Criar grupo | ✅ |
| `GET` | `/api/v1/grupos-empresa/{id}/` | Detalhar grupo | ✅ |
| `POST` | `/api/v1/clientes/chat/buscar-contato/` | Buscar contato (chat) | ❌ |
| `POST` | `/api/v1/clientes/chat/dados-capturados/` | Salvar dados do chat | ❌ |
| `POST` | `/api/v1/clientes/cadastro-manual/` | Cadastro manual | ✅ |

---

## 📞 Contatos

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/api/v1/contatos/` | Listar contatos | ✅ |
| `POST` | `/api/v1/contatos/` | Criar contato | ✅ |
| `GET` | `/api/v1/contatos/{id}/` | Detalhar contato | ✅ |
| `PUT` | `/api/v1/contatos/{id}/` | Atualizar contato | ✅ |
| `PATCH` | `/api/v1/contatos/{id}/` | Atualizar parcial | ✅ |
| `DELETE` | `/api/v1/contatos/{id}/` | Deletar contato | ✅ |

---

## 📄 Documentos

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/api/v1/documentos/` | Listar documentos | ✅ |
| `POST` | `/api/v1/documentos/` | Upload documento | ✅ |
| `GET` | `/api/v1/documentos/{id}/` | Detalhar documento | ✅ |
| `PUT` | `/api/v1/documentos/{id}/` | Atualizar documento | ✅ |
| `PATCH` | `/api/v1/documentos/{id}/` | Atualizar parcial | ✅ |
| `DELETE` | `/api/v1/documentos/{id}/` | Deletar documento | ✅ |
| `POST` | `/api/v1/documentos/gerar-contrato/` | Gerar contrato automático | ✅ |
| `POST` | `/api/v1/documentos/gerar-boleto/` | Gerar boleto | ✅ |

---

## 💬 WhatsApp

### Sessões (9 endpoints)

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/api/v1/whatsapp/sessions/` | Listar sessões | ✅ |
| `POST` | `/api/v1/whatsapp/sessions/` | Criar sessão | ✅ |
| `GET` | `/api/v1/whatsapp/sessions/{id}/` | Detalhar sessão | ✅ |
| `POST` | `/api/v1/whatsapp/sessions/start/` | Iniciar sessão | ✅ |
| `POST` | `/api/v1/whatsapp/sessions/stop/` | Parar sessão | ✅ |
| `GET` | `/api/v1/whatsapp/sessions/status/` | Status da sessão | ✅ |
| `GET` | `/api/v1/whatsapp/sessions/{id}/metrics/` | Métricas da sessão | ✅ |
| `GET` | `/api/v1/whatsapp/sessions/{id}/export/` | Exportar sessão | ✅ |
| `POST` | `/api/v1/whatsapp/sessions/import/` | Importar sessão | ✅ |
| `POST` | `/api/v1/whatsapp/sessions/{id}/reconnect/` | Forçar reconexão | ✅ |

### Mensagens (9 endpoints)

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/api/v1/whatsapp/messages/` | Listar mensagens | ✅ |
| `GET` | `/api/v1/whatsapp/messages/{id}/` | Detalhar mensagem | ✅ |
| `POST` | `/api/v1/whatsapp/send/` | Enviar mensagem | ✅ |
| `GET` | `/api/v1/whatsapp/messages/high-latency/` | Mensagens alta latência | ✅ |
| `GET` | `/api/v1/whatsapp/messages/latency-stats/` | Estatísticas latência | ✅ |
| `POST` | `/api/v1/whatsapp/webhook/` | Webhook mensagens | ❌ |
| `POST` | `/api/v1/whatsapp/messages` | Enviar (legacy) | ✅ |
| `POST` | `/api/v1/whatsapp/session/start` | Iniciar (legacy) | ✅ |
| `POST` | `/api/v1/whatsapp/session` | Parar (legacy) | ✅ |
| `GET` | `/api/v1/whatsapp/session/status` | Status (legacy) | ✅ |

---

## 💬 Chats

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/api/v1/chats/` | Listar conversas | ✅ |
| `GET` | `/api/v1/chats/{chat_id}/` | Detalhar conversa | ✅ |
| `GET` | `/api/v1/chats/{chat_id}/messages/` | Mensagens do chat | ✅ |
| `POST` | `/api/v1/chats/{chat_id}/aceitar/` | Aceitar atendimento | ✅ |
| `POST` | `/api/v1/chats/{chat_id}/transferir/` | Transferir chat | ✅ |
| `POST` | `/api/v1/chats/{chat_id}/encerrar/` | Encerrar chat | ✅ |

---

## 🎫 Atendimento

### Departamentos (5 endpoints)

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/api/v1/atendimento/departamentos/` | Listar departamentos | ✅ |
| `POST` | `/api/v1/atendimento/departamentos/` | Criar departamento | ✅ |
| `GET` | `/api/v1/atendimento/departamentos/{id}/` | Detalhar departamento | ✅ |
| `PUT` | `/api/v1/atendimento/departamentos/{id}/` | Atualizar departamento | ✅ |
| `PATCH` | `/api/v1/atendimento/departamentos/{id}/` | Atualizar parcial | ✅ |

### Filas (5 endpoints)

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/api/v1/atendimento/filas/` | Listar filas | ✅ |
| `POST` | `/api/v1/atendimento/filas/` | Adicionar na fila | ✅ |
| `GET` | `/api/v1/atendimento/filas/{id}/` | Detalhar fila | ✅ |
| `DELETE` | `/api/v1/atendimento/filas/{id}/` | Remover da fila | ✅ |
| `POST` | `/api/v1/atendimento/filas/distribuir/` | Distribuir automaticamente | ✅ |

### Atendimentos (8 endpoints)

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/api/v1/atendimento/atendimentos/` | Listar atendimentos | ✅ |
| `POST` | `/api/v1/atendimento/atendimentos/` | Criar atendimento | ✅ |
| `GET` | `/api/v1/atendimento/atendimentos/{id}/` | Detalhar atendimento | ✅ |
| `PATCH` | `/api/v1/atendimento/atendimentos/{id}/` | Atualizar atendimento | ✅ |
| `GET` | `/api/v1/atendimento/atendimentos/meus-atendimentos/` | Meus atendimentos | ✅ |
| `POST` | `/api/v1/atendimento/atendimentos/{id}/finalizar/` | Finalizar atendimento | ✅ |
| `POST` | `/api/v1/atendimento/atendimentos/{id}/avaliar/` | Avaliar atendimento | ✅ |
| `POST` | `/api/v1/atendimento/atendimentos/{id}/transferir/` | Transferir atendimento | ✅ |

---

## 🔔 Notificações e Presença

### Preferências (2 endpoints)

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/api/v1/me/preferencias-notificacao/` | Obter preferências | ✅ |
| `PATCH` | `/api/v1/me/preferencias-notificacao/` | Atualizar preferências | ✅ |

### Presença (3 endpoints)

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/api/v1/presence/me/` | Meu status | ✅ |
| `POST` | `/api/v1/presence/set-status/` | Alterar status | ✅ |
| `POST` | `/api/v1/presence/heartbeat/` | Heartbeat (keep alive) | ✅ |

### Digitação (2 endpoints)

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `POST` | `/api/v1/typing/` | Indicar digitando | ✅ |
| `DELETE` | `/api/v1/typing/` | Parar de digitar | ✅ |

---

## ⚙️ Configurações

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/api/v1/config/` | Todas configurações | ✅ |
| `GET` | `/api/v1/config/company/` | Config empresa | ✅ |
| `PATCH` | `/api/v1/config/company/` | Atualizar empresa | ✅ |
| `GET` | `/api/v1/config/chat/` | Config chat | ✅ |
| `PATCH` | `/api/v1/config/chat/` | Atualizar chat | ✅ |
| `GET` | `/api/v1/config/email/` | Config email | ✅ |
| `PATCH` | `/api/v1/config/email/` | Atualizar email | ✅ |
| `GET` | `/api/v1/config/appearance/` | Config aparência | ✅ |
| `PATCH` | `/api/v1/config/appearance/` | Atualizar aparência | ✅ |
| `POST` | `/api/v1/config/appearance/upload/` | Upload logo/imagens | ✅ |
| `GET` | `/api/v1/config/whatsapp/` | Config WhatsApp | ✅ |

---

## 🌐 Integrações

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/api/v1/integrations/cep/{cep}/` | Consultar CEP | ❌ |

---

## 🔐 Permissões e Grupos

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/api/v1/authz/permissions/` | Listar permissões | ✅ |
| `GET` | `/api/v1/authz/groups/` | Listar grupos | ✅ |
| `POST` | `/api/v1/authz/groups/` | Criar grupo | ✅ |
| `GET` | `/api/v1/authz/groups/{id}/` | Detalhar grupo | ✅ |
| `PUT` | `/api/v1/authz/groups/{id}/` | Atualizar grupo | ✅ |
| `DELETE` | `/api/v1/authz/groups/{id}/` | Deletar grupo | ✅ |
| `GET` | `/api/v1/authz/agents/{id}/groups/` | Grupos de um agente | ✅ |

---

## 🔌 WebSocket

| Protocolo | Endpoint | Descrição | Auth |
|-----------|----------|-----------|------|
| `WS` | `ws://localhost:8001/ws/whatsapp/?token={jwt}` | Eventos WhatsApp | ✅ |
| `WS` | `ws://localhost:8001/ws/atendimento/?token={jwt}` | Eventos Atendimento | ✅ |

### Eventos Disponíveis

**WhatsApp:**
- `session_status` - Mudança de status
- `qrcode` - QR Code disponível
- `message_received` - Nova mensagem
- `message_status` - Status atualizado

**Atendimento:**
- `message_received` - Nova mensagem
- `message_sent` - Mensagem enviada
- `chat_assigned` - Atendimento atribuído
- `chat_transferred` - Atendimento transferido
- `chat_auto_closed` - Encerramento automático
- `agent_presence_changed` - Mudança de presença
- `typing_start` / `typing_stop` - Digitação

---

## 📚 Documentação

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/api/schema/` | Schema OpenAPI | ❌ |
| `GET` | `/api/docs/` | Swagger UI | ❌ |
| `GET` | `/api/redoc/` | ReDoc | ❌ |
| `GET` | `/api/v1/health/` | Health check | ❌ |

---

## 📝 Notas Importantes

### Autenticação

- Maioria dos endpoints requer autenticação JWT
- Token obtido via `/api/v1/auth/token/`
- Header: `Authorization: Bearer {token}`
- Exceções: CEP, chat integration, webhook, docs

### Paginação

Endpoints que retornam listas suportam paginação:
```json
{
  "count": 100,
  "next": "http://...?page=2",
  "previous": null,
  "results": [...]
}
```

### Filtros Comuns

- `search` - Busca textual
- `ordering` - Ordenação (use `-` para desc)
- `page` - Número da página
- `page_size` - Itens por página

### Códigos de Status HTTP

- `200` - OK
- `201` - Criado
- `202` - Aceito (async)
- `204` - Sem conteúdo
- `400` - Requisição inválida
- `401` - Não autenticado
- `403` - Sem permissão
- `404` - Não encontrado
- `423` - Recurso bloqueado
- `500` - Erro interno

---

## 🚀 Quick Start

### 1. Obter Token
```bash
curl -X POST http://localhost:8001/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "senha"}'
```

### 2. Usar Token
```bash
curl -X GET http://localhost:8001/api/v1/clientes/ \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

### 3. Conectar WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8001/ws/whatsapp/?token=SEU_TOKEN');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

---

## 📖 Documentações Relacionadas

- [API Reference Completa](./API_REFERENCE.md)
- [WhatsApp - Sessões e Eventos](./WHATSAPP_SESSION_EVENTS.md)
- [Eventos de Notificação](./NOTIFICATION_EVENTS.md)
- [Guia de Testes com Stub](./WHATSAPP_STUB_TESTING.md)
- [Integração CEP](./CEP_INTEGRATION.md)
- [Configuração CORS](./CORS_CONFIGURATION.md)
- [Variáveis de Ambiente](./ENVIRONMENT_VARIABLES.md)

---

**Versão**: v1  
**Última Atualização**: 12/10/2025  
**Total de Endpoints**: 100  
**Status**: ✅ Produção

