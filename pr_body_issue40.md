# PR: Encerramento Automático por Inatividade (Issue #40)

## 📋 Descrição

Implementação de sistema de encerramento automático de atendimentos inativos via Celery Beat com notificações WebSocket.

Fecha #40

---

## ✨ Funcionalidades Implementadas

### 1. **Task Celery Periódica**
`encerrar_atendimentos_inativos()` - Executa periodicamente para verificar e encerrar chats inativos.

**Comportamento:**
- Busca configuração `timeout_inatividade_minutos` em `chat_settings`
- Padrão: 30 minutos
- Verifica atendimentos em `em_atendimento` sem atualização
- Encerra automaticamente com observação
- Emite evento WebSocket

### 2. **Evento WebSocket `chat_auto_closed`**
```json
{
  "event": "chat_auto_closed",
  "data": {
    "atendimento_id": 123,
    "cliente_nome": "Empresa XYZ",
    "chat_id": "5511999999999",
    "motivo": "inatividade",
    "tempo_inativo_minutos": 45,
    "timestamp": "2025-10-11T20:00:00Z"
  },
  "version": "v1"
}
```

### 3. **Logs Estruturados**
```
INFO: [Task] Verificando atendimentos inativos para encerramento automático
INFO: Atendimento 123 encerrado automaticamente (cliente: Empresa XYZ, inatividade: 45min)
INFO: [Task] Encerramento automático concluído: 3 atendimentos encerrados (timeout: 30min)
```

---

## ⚙️ Configuração

### 1. **Config - chat_settings**
```json
{
  "timeout_inatividade_minutos": 30,
  "mensagem_encerramento": "Atendimento encerrado por inatividade."
}
```

### 2. **Celery Beat Schedule**
Adicionar ao `config/celery.py`:
```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'encerrar-atendimentos-inativos': {
        'task': 'atendimento.tasks.encerrar_atendimentos_inativos',
        'schedule': crontab(minute='*/10'),  # A cada 10 minutos
    },
}
```

---

## 🔄 Fluxo de Funcionamento

```
1. Task executa a cada 10 minutos
    ↓
2. Busca timeout_inatividade_minutos (Config)
    ↓
3. Calcula cutoff_time = now - timeout
    ↓
4. Busca atendimentos em_atendimento
    ↓
5. Filtra atualizado_em < cutoff_time
    ↓
6. Para cada atendimento inativo:
    - Calcula tempo de inatividade
    - Finaliza com observação
    - Emite evento WebSocket
    - Loga encerramento
    ↓
7. Retorna quantidade encerrada
```

---

## 📊 Exemplo de Uso

### Timeline
```
10:00 - Cliente envia última mensagem
10:30 - Timeout de 30min atingido
10:40 - Task verifica (executa a cada 10min)
10:40 - Atendimento encerrado automaticamente
10:40 - Atendente recebe notificação WebSocket
```

### Log Completo
```
INFO: [Task] Verificando atendimentos inativos para encerramento automático
INFO: Atendimento 100 encerrado automaticamente (cliente: ABC Ltda, inatividade: 32min)
INFO: Atendimento 101 encerrado automaticamente (cliente: XYZ SA, inatividade: 45min)
INFO: [Task] Encerramento automático concluído: 2 atendimentos encerrados (timeout: 30min)
```

---

## 🎯 Critérios de Aceitação (Issue #40)

- [x] ✅ Usa `chat_settings.timeout_inatividade_minutos`
- [x] ✅ Task periódica Celery
- [x] ✅ Mensagem/observação de encerramento
- [x] ✅ Registro de evento (logs)
- [x] ✅ Notificação WebSocket

---

## 🚀 Deploy

### 1. Configurar timeout
```python
from core.models import Config

config = Config.objects.first()
config.chat_settings = {
    'timeout_inatividade_minutos': 30
}
config.save()
```

### 2. Configurar Celery Beat
Editar `config/celery.py` e adicionar schedule (ver acima).

### 3. Reiniciar Beat
```bash
docker-compose restart beat
```

---

## 🔗 Referências

- **Issue**: #40 - Encerramento automático por inatividade
- **Sprint**: 3

---

**Desenvolvido com ❤️ para o DX Connect**

