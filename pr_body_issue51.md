# PR: Gestão de Estado das Sessões de Chat (Presença do Atendente) (Issue #51)

## 📋 Descrição

🎉 **ÚLTIMA ISSUE DA SPRINT 3!** 

Sistema completo de gestão de presença de atendentes com status online/offline/busy, indicadores de digitação em tempo real e heartbeat automático.

Fecha #51

---

## ✨ Funcionalidades Implementadas

### 1. **Modelo AgentPresence**
- ✅ Status: online, offline, busy, away
- ✅ Mensagem de status personalizada
- ✅ Heartbeat automático
- ✅ Controle de sessão WebSocket
- ✅ Timestamps de mudança de status

### 2. **Modelo TypingIndicator**
- ✅ Indicadores de digitação por chat
- ✅ Eventos typing_start/typing_stop
- ✅ Detecção de travamento (>30s)

### 3. **Endpoints**
- `GET /api/v1/presence/me/`: Minha presença
- `POST /api/v1/presence/set-status/`: Alterar status
- `POST /api/v1/presence/heartbeat/`: Atualizar heartbeat
- `POST /api/v1/typing/`: Indicar que está digitando
- `DELETE /api/v1/typing/?chat_id=xxx`: Parar de digitar

### 4. **Task Celery de Timeout**
`check_agent_presence_timeout()` - Marca agentes como offline após 2min sem heartbeat.

### 5. **Eventos WebSocket**

#### agent_presence_changed
```json
{
  "event": "agent_presence_changed",
  "data": {
    "agent_id": 5,
    "status": "online",
    "message": "Disponível",
    "timestamp": "2025-10-11T21:00:00Z"
  },
  "version": "v1"
}
```

#### typing_start / typing_stop
```json
{
  "event": "typing_start",
  "data": {
    "chat_id": "5511999999999",
    "from": "João Silva",
    "timestamp": "2025-10-11T21:00:00Z"
  },
  "version": "v1"
}
```

---

## 🔄 Fluxo de Presença

### Online
```
1. Atendente abre aplicação
2. WebSocket conecta
3. POST /presence/set-status/ {status: "online"}
4. Presença criada/atualizada
5. Evento broadcast para todos
6. Heartbeat a cada 30s (POST /presence/heartbeat/)
```

### Offline por Timeout
```
1. Atendente perde conexão
2. Heartbeat para de chegar
3. Task Celery verifica (a cada minuto)
4. Detecta sem heartbeat há >2min
5. Marca como offline
6. Emite evento de mudança de status
```

### Indicador de Digitação
```
1. Atendente começa a digitar
2. POST /typing/ {chat_id: "xxx"}
3. Evento typing_start broadcast
4. Frontend mostra "Digitando..."
5. DELETE /typing/?chat_id=xxx
6. Evento typing_stop broadcast
7. Frontend remove indicador
```

---

## 📊 Campos AgentPresence

| Campo | Tipo | Descrição |
|-------|------|-----------|
| agent | FK | Agente/Atendente |
| status | CharField | online/offline/busy/away |
| status_message | CharField | Mensagem personalizada |
| last_heartbeat | DateTime | Último ping recebido |
| websocket_connected | Boolean | Se WS está conectado |
| status_changed_at | DateTime | Quando mudou de status |

**Propriedades:**
- `is_available`: True se online e conectado
- `tempo_no_status_atual`: Minutos no status
- `esta_inativo`: True se sem heartbeat >2min

---

## 🔧 Uso da API

### Alterar Status
```bash
curl -X POST http://localhost:8001/api/v1/presence/set-status/ \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "status": "busy",
    "message": "Em reunião até 15h"
  }'
```

### Heartbeat (Manter Vivo)
```bash
curl -X POST http://localhost:8001/api/v1/presence/heartbeat/ \
  -H "Authorization: Bearer $TOKEN"
```

### Indicar Digitação
```bash
# Começar
curl -X POST http://localhost:8001/api/v1/typing/ \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"chat_id": "5511999999999"}'

# Parar
curl -X DELETE http://localhost:8001/api/v1/typing/?chat_id=5511999999999 \
  -H "Authorization: Bearer $TOKEN"
```

---

## ⚙️ Configuração Celery Beat

Adicionar ao `config/celery.py`:
```python
app.conf.beat_schedule = {
    'check-agent-presence': {
        'task': 'accounts.tasks.check_agent_presence_timeout',
        'schedule': crontab(minute='*/1'),  # A cada minuto
    },
}
```

---

## 📂 Arquivos Criados

- `accounts/models_presence.py`: AgentPresence, TypingIndicator
- `accounts/serializers_presence.py`: Serializers
- `accounts/views_presence.py`: ViewSets e views
- `accounts/tasks.py`: Task de timeout
- `accounts/migrations/0004_add_agent_presence_typing.py`

---

## 📂 Arquivos Modificados

- `accounts/models.py`: Imports
- `config/urls.py`: Rotas de presença

---

## 🎯 Critérios de Aceitação (Issue #51)

- [x] ✅ Endpoints para consultar e alterar status
- [x] ✅ Eventos WS para presença e typing
- [x] ✅ Timeout para marcar offline automático
- [x] ✅ Heartbeat do cliente
- [x] ✅ Controle de sessões ativas/inativas

---

## 🚀 Deploy

```bash
docker-compose exec web python manage.py migrate
docker-compose restart worker beat
```

---

## 🎉 **SPRINT 3 - 100% COMPLETA!**

Esta é a **ÚLTIMA ISSUE** da Sprint 3! Com este PR, completamos:

✅ 10/10 issues da Sprint 3
✅ ~11.000 linhas de código
✅ Sistema de atendimento completo
✅ Sistema WhatsApp robusto
✅ Filas, transferências, notificações, presença

**PARABÉNS!** 🏆🎊

---

## 🔗 Referências

- **Issue**: #51 - Gestão de Estado das Sessões
- **Sprint**: 3 - Atendimento via Chat
- **Status**: ÚLTIMA ISSUE! 🎯

---

**Desenvolvido com ❤️ para o DX Connect - Sprint 3 COMPLETA!** 🎉

