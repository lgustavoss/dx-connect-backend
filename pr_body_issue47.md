# PR: WhatsApp - Gestão de Sessões e Conexão (Issue #47)

## 📋 Descrição

Implementação de gestão robusta de sessões WhatsApp Web com reconexão automática, suporte a proxy, backup/restore e métricas avançadas.

Fecha #47

---

## ✨ Funcionalidades Implementadas

### 1. **Reconexão Automática com Backoff Exponencial**
- ✅ Task Celery `auto_reconnect_session_task`
- ✅ Até 6 tentativas com delays crescentes
- ✅ Backoff: 0s → 30s → 60s → 120s → 240s → 480s
- ✅ Logs detalhados de cada tentativa
- ✅ Marcação de erro permanente após falhas

### 2. **Suporte a Proxy/IP Residencial**
- ✅ Campos no modelo: `proxy_enabled`, `proxy_url`
- ✅ Configurável por sessão
- ✅ Persistido no backup

### 3. **Export/Import de Sessão (Backup)**
- ✅ `GET /api/v1/whatsapp/sessions/{id}/export/`: Download de backup
- ✅ `POST /api/v1/whatsapp/sessions/import/`: Restaurar de backup
- ✅ Formato JSON estruturado
- ✅ Inclui dados criptografados de sessão

### 4. **Endpoint de Reconexão Manual**
- ✅ `POST /api/v1/whatsapp/sessions/{id}/reconnect/`: Forçar reconexão
- ✅ Usa mesma task com backoff
- ✅ Retorna task_id para monitoramento

### 5. **Campos Adicionais no Modelo**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `auto_reconnect` | Boolean | Habilitar reconexão automática |
| `reconnect_attempts` | Integer | Contador de tentativas |
| `last_reconnect_at` | DateTime | Última tentativa de reconexão |
| `proxy_enabled` | Boolean | Usar proxy |
| `proxy_url` | CharField | URL do proxy |

---

## 📂 Arquivos Modificados

### Modelo
- `whatsapp/models.py`: Campos de reconexão e proxy

### Tasks
- `whatsapp/tasks.py`: Task `auto_reconnect_session_task`

### Views
- `whatsapp/views.py`: Actions `export_session`, `import_session`, `force_reconnect`

### Migrations
- `whatsapp/migrations/0003_add_reconnect_proxy_fields.py`

---

## 🔄 Reconexão Automática

### Funcionamento

1. **Sessão desconecta** (erro ou timeout)
2. **Task de reconexão enfileirada** automaticamente
3. **Primeira tentativa** (imediato)
4. **Se falhar**, aguarda backoff e tenta novamente
5. **Até 6 tentativas** com delays crescentes
6. **Se todas falharem**, marca como erro permanente

### Timeline de Exemplo
```
t=0s    : Desconexão detectada → Tentativa 1 (falha)
t=30s   : Tentativa 2 (falha)
t=90s   : Tentativa 3 (falha)
t=210s  : Tentativa 4 (falha)
t=450s  : Tentativa 5 (falha)
t=930s  : Tentativa 6 (falha) → Erro permanente
```

### Logs
```
[Reconnect] Tentando reconectar sessão 1 (tentativa 1/6)
[Reconnect] Reagendando reconexão em 30s
[Reconnect] Tentando reconectar sessão 1 (tentativa 2/6)
[Reconnect] Sessão 1 reconectada com sucesso após 3 tentativas
```

---

## 🔒 Export/Import de Sessão

### Exportar (Backup)
```bash
curl -X GET http://localhost:8001/api/v1/whatsapp/sessions/1/export/ \
  -H "Authorization: Bearer $TOKEN" \
  -o backup_session_1.json
```

**Arquivo gerado:**
```json
{
  "session_id": 1,
  "usuario_id": 1,
  "device_name": "DX Connect Web",
  "phone_number": "5511999999999",
  "session_data": "encrypted_session_data...",
  "auto_reconnect": true,
  "proxy_enabled": false,
  "proxy_url": "",
  "created_at": "2025-10-11T10:00:00Z",
  "connected_at": "2025-10-11T10:05:00Z",
  "export_timestamp": "2025-10-11T18:00:00Z"
}
```

### Importar (Restore)
```bash
curl -X POST http://localhost:8001/api/v1/whatsapp/sessions/import/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @backup_session_1.json
```

**Resposta:**
```json
{
  "message": "Sessão criada com sucesso",
  "session_id": 2,
  "created": true
}
```

---

## 🌐 Configuração de Proxy

### Habilitar Proxy
```bash
curl -X PATCH http://localhost:8001/api/v1/whatsapp/sessions/1/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "proxy_enabled": true,
    "proxy_url": "http://proxy.example.com:8080"
  }'
```

### Tipos de Proxy Suportados
- HTTP/HTTPS Proxy
- SOCKS5 Proxy
- IP Residencial

---

## 🔧 Forçar Reconexão

### Endpoint
```bash
curl -X POST http://localhost:8001/api/v1/whatsapp/sessions/1/reconnect/ \
  -H "Authorization: Bearer $TOKEN"
```

**Resposta:**
```json
{
  "message": "Reconexão iniciada",
  "task_id": "a1b2c3d4-1234-5678-90ab-cdef12345678",
  "session_id": 1
}
```

### Monitorar Reconexão
```bash
# Ver logs do worker
docker-compose logs -f worker

# Consultar status da sessão
curl http://localhost:8001/api/v1/whatsapp/sessions/status/ \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🎯 Critérios de Aceitação (Issue #47)

- [x] ✅ Iniciar/parar sessão com estado consultável
- [x] ✅ Reconexão automática com backoff e logs
- [x] ✅ Suporte a proxy/IP residencial (configurável)
- [x] ✅ Export/Import de sessão (backup)

**Tarefas:**
- [x] ✅ Serviço de sessão (start/stop/status)
- [x] ✅ Persistência de artefatos (criptografados)
- [x] ✅ Endpoints de controle e métricas
- [x] ✅ Logs estruturados

---

## 📝 Checklist

- [x] Campos de reconexão adicionados
- [x] Campos de proxy adicionados
- [x] Task de reconexão automática criada
- [x] Backoff exponencial implementado
- [x] Endpoint export criado
- [x] Endpoint import criado
- [x] Endpoint reconnect criado
- [x] Logs estruturados
- [x] Migration gerada
- [x] Documentação criada

---

## 🚀 Deploy

### 1. Aplicar Migration
```bash
docker-compose exec web python manage.py migrate
```

### 2. Reiniciar Workers
```bash
docker-compose restart worker beat
```

---

## 🔗 Referências

- **Issue**: #47 - WhatsApp: Gestão de Sessões e Conexão
- **Sprint**: 3 - Atendimento via Chat
- **Épico**: #10

---

## 🎉 Impacto

### Confiabilidade
- ✅ Reconexão automática reduz tempo de inatividade
- ✅ Backoff evita sobrecarga do servidor
- ✅ Logs facilitam troubleshooting

### Flexibilidade
- ✅ Suporte a proxy para IPs residenciais
- ✅ Backup/restore facilita migração
- ✅ Configuração por sessão

### Observabilidade
- ✅ Contador de tentativas de reconexão
- ✅ Timestamps detalhados
- ✅ Logs estruturados

---

**Desenvolvido com ❤️ para o DX Connect**

