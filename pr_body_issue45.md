# PR: WhatsApp - Envio de Mensagens com Fila (Issue #45)

## 📋 Descrição

Implementação de sistema de fila para envio de mensagens WhatsApp com retentativas automáticas via Celery e eventos WebSocket de confirmação.

Fecha #45

---

## ✨ Funcionalidades Implementadas

### 1. **Task Celery para Fila de Envio**
- ✅ Task `send_whatsapp_message_task` com retentativas automáticas
- ✅ Máximo 3 tentativas com backoff exponencial
- ✅ Delay inicial de 60s entre retentativas
- ✅ Backoff máximo de 10 minutos
- ✅ Jitter aleatório para evitar sobrecarga

### 2. **Sistema de Retentativas**
```python
@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
```

### 3. **Evento WebSocket `message_sent`**
Formato padronizado v1:
```json
{
  "event": "message_sent",
  "data": {
    "message_id": "abc123",
    "status": "queued",
    "to": "5511999999999",
    "timestamp": "2025-10-11T18:00:00Z",
    "error": null
  },
  "version": "v1"
}
```

### 4. **Endpoint Atualizado**
`POST /api/v1/whatsapp/send/` agora:
- Enfileira mensagem para envio assíncrono
- Retorna imediatamente com `task_id`
- Não bloqueia a requisição HTTP

**Resposta:**
```json
{
  "message": "Mensagem enfileirada para envio",
  "task_id": "a1b2c3d4-1234-5678-90ab-cdef12345678",
  "to": "5511999999999",
  "client_message_id": "custom_id_123",
  "status": "queued"
}
```

### 5. **Task de Limpeza Periódica**
- `cleanup_old_message_queue`: Remove mensagens com erro após 7 dias
- Execução agendada via Celery Beat

---

## 📂 Arquivos Criados

### Tasks Celery
- `whatsapp/tasks.py`: Tasks de envio e limpeza

---

## 📂 Arquivos Modificados

### Views
- `whatsapp/views.py`: `WhatsAppSendMessageView` usa fila Celery

---

## 🔄 Fluxo de Envio

1. **Cliente faz POST** `/api/v1/whatsapp/send/`
2. **API valida payload** (campos obrigatórios, formato)
3. **Mensagem enfileirada** via Celery (`apply_async`)
4. **Retorna task_id** imediatamente (não bloqueia)
5. **Worker Celery processa** a fila
6. **Tenta enviar** via `WhatsAppSessionService`
7. **Se falhar**, aguarda e retenta (até 3x)
8. **Emite evento WS** `message_sent` com status
9. **Se sucesso**, status = `queued`
10. **Se falha final**, status = `failed`

---

## 🔁 Sistema de Retentativas

### Configuração
- **Tentativas**: 3 (total de 4 envios incluindo inicial)
- **Delay inicial**: 60 segundos
- **Backoff**: Exponencial com jitter
- **Delay máximo**: 600 segundos (10 minutos)

### Exemplo de Timeline
```
Tentativa 1: Imediato (t=0s)
    ↓ Falha
Tentativa 2: ~60s depois (t=60s)
    ↓ Falha
Tentativa 3: ~120s depois (t=180s)
    ↓ Falha
Tentativa 4: ~240s depois (t=420s)
    ↓ Falha → Marca como "failed"
```

### Em Caso de Falha Final
- Mensagem marcada como `error` no banco
- Evento WebSocket com `status: "failed"`
- Log de erro detalhado

---

## 📡 Eventos WebSocket

### message_sent (Sucesso)
```json
{
  "event": "message_sent",
  "data": {
    "message_id": "msg_123",
    "status": "queued",
    "to": "5511999999999",
    "timestamp": "2025-10-11T18:00:00.123Z",
    "error": null
  },
  "version": "v1"
}
```

### message_sent (Falha)
```json
{
  "event": "message_sent",
  "data": {
    "message_id": "msg_123",
    "status": "failed",
    "to": "5511999999999",
    "timestamp": "2025-10-11T18:07:30.456Z",
    "error": "Sessão não está pronta para enviar mensagens"
  },
  "version": "v1"
}
```

---

## 🧪 Uso

### Enviar Mensagem
```bash
curl -X POST http://localhost:8001/api/v1/whatsapp/send/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "5511999999999",
    "type": "text",
    "text": "Olá! Mensagem via fila",
    "client_message_id": "custom_123"
  }'
```

### Resposta
```json
{
  "message": "Mensagem enfileirada para envio",
  "task_id": "a1b2c3d4-1234-5678-90ab-cdef12345678",
  "to": "5511999999999",
  "client_message_id": "custom_123",
  "status": "queued"
}
```

### Monitorar via WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8001/ws/whatsapp/?token=YOUR_JWT');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.event === 'message_sent') {
    console.log('Mensagem enviada:', data.data.message_id);
    console.log('Status:', data.data.status);
    
    if (data.data.error) {
      console.error('Erro:', data.data.error);
    }
  }
};
```

---

## ⚙️ Configuração Celery

### Celery Beat (Tarefas Periódicas)
Adicionar ao `config/celery.py`:
```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'cleanup-old-messages': {
        'task': 'whatsapp.tasks.cleanup_old_message_queue',
        'schedule': crontab(hour=3, minute=0),  # Diariamente às 3h
    },
}
```

### Iniciar Workers
```bash
# Worker principal
celery -A config worker -l INFO

# Beat (agendador)
celery -A config beat -l INFO
```

---

## 📊 Monitoramento

### Logs
```
[Task] Enviando mensagem para 5511999999999 (usuário: 1, tentativa: 1/4)
[Task] Mensagem enviada com sucesso: msg_123 (tentativa: 1)
```

### Em Caso de Erro
```
[Task] Erro ao enviar mensagem (tentativa 1): session_not_ready
[Task] Erro ao enviar mensagem (tentativa 2): session_not_ready
[Task] Erro ao enviar mensagem (tentativa 3): session_not_ready
[Task] Mensagem falhou definitivamente após 4 tentativas
```

---

## 🎯 Critérios de Aceitação (Issue #45)

- [x] ✅ Fila/retentativas para envio implementada (Celery)
- [x] ✅ Evento WS `message_sent` com `message_id` e status
- [x] ✅ Validação de payload (serializer DRF)
- [x] ✅ Validação de permissões (IsAuthenticated)

---

## 📝 Checklist

- [x] Task Celery criada
- [x] Sistema de retentativas configurado
- [x] Evento `message_sent` implementado
- [x] Endpoint atualizado para usar fila
- [x] Task de limpeza periódica criada
- [x] Logs estruturados
- [x] Documentação criada
- [ ] Testes atualizados (requer mock do Celery)

---

## ⚠️ Limitações Conhecidas

1. **Testes**: Requerem mock do Celery (Redis não disponível em ambiente de teste)
2. **Monitoramento**: Recomenda-se usar Flower para monitorar filas Celery
3. **Escala**: Para alta carga, considerar múltiplos workers

---

## 🚀 Deploy

### 1. Reiniciar Workers Celery
```bash
# Parar workers existentes
docker-compose stop worker beat

# Rebuild e iniciar
docker-compose up -d --build worker beat
```

### 2. Verificar Workers
```bash
docker-compose logs -f worker
```

### 3. Testar Envio
```bash
curl -X POST https://api.seudominio.com/api/v1/whatsapp/send/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @test_message.json
```

---

## 🔗 Referências

- **Issue**: #45 - WhatsApp: Envio de Mensagens
- **Sprint**: 3 - Atendimento via Chat
- **Issues Anteriores**: #36, #44

---

## 🎉 Próximos Passos

1. **Issue #46**: WhatsApp: Processamento de Mídias
2. **Issue #47**: WhatsApp: Gestão de Sessões e Conexão (avançado)
3. Adicionar Flower para monitoramento de filas

---

**Desenvolvido com ❤️ para o DX Connect**

