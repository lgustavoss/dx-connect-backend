# WhatsApp - Sessões e Eventos (Issue #36)

## 📋 Índice
- [Visão Geral](#visão-geral)
- [Modelos de Dados](#modelos-de-dados)
- [Endpoints API](#endpoints-api)
- [WebSocket](#websocket)
- [Métricas de Latência](#métricas-de-latência)
- [Exemplos de Uso](#exemplos-de-uso)

---

## 🎯 Visão Geral

Sistema completo de gerenciamento de sessões WhatsApp Web com persistência em banco de dados e métricas de latência em tempo real.

### Funcionalidades Implementadas

✅ **Modelos de Persistência**
- `WhatsAppSession`: Gerenciamento de sessões WhatsApp
- `WhatsAppMessage`: Histórico completo de mensagens

✅ **Gestão de Sessões**
- Iniciar/Parar sessões WhatsApp
- Consultar status em tempo real
- Rastreamento de uptime e métricas

✅ **Mensagens**
- Envio de mensagens (texto, imagem, áudio, etc)
- Recebimento e persistência de mensagens
- Atualização de status (queued → sent → delivered → read)

✅ **Métricas de Latência**
- Cálculo automático de latência em milissegundos
- Alertas para latências > 5 segundos
- Estatísticas agregadas de desempenho

✅ **WebSocket em Tempo Real**
- Eventos de sessão (connecting, qrcode, ready, etc)
- Eventos de mensagens
- Persistência automática no banco

---

## 📊 Modelos de Dados

### WhatsAppSession

Representa uma sessão WhatsApp Web conectada.

#### Campos Principais

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `usuario` | FK | Usuário responsável pela sessão |
| `status` | CharField | Status da sessão (disconnected, connecting, qrcode, authenticated, ready, error) |
| `device_name` | CharField | Nome do dispositivo conectado |
| `phone_number` | CharField | Número do WhatsApp conectado |
| `qr_code` | TextField | QR Code em base64 (quando disponível) |
| `connected_at` | DateTime | Data/hora da última conexão |
| `total_messages_sent` | Integer | Total de mensagens enviadas |
| `total_messages_received` | Integer | Total de mensagens recebidas |
| `error_count` | Integer | Contador de erros |

#### Propriedades

- `is_connected`: Retorna `True` se status == 'ready' e is_active == True
- `uptime_seconds`: Tempo de atividade desde a conexão em segundos

#### Métodos

- `mark_as_connected()`: Marca sessão como conectada (ready)
- `mark_as_disconnected()`: Marca sessão como desconectada
- `mark_as_error(error_message)`: Marca sessão com erro
- `increment_sent_messages()`: Incrementa contador de mensagens enviadas
- `increment_received_messages()`: Incrementa contador de mensagens recebidas

---

### WhatsAppMessage

Representa uma mensagem enviada ou recebida via WhatsApp.

#### Campos Principais

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `session` | FK | Sessão WhatsApp associada |
| `usuario` | FK | Usuário responsável |
| `message_id` | CharField | ID único da mensagem |
| `direction` | CharField | Direção (inbound/outbound) |
| `message_type` | CharField | Tipo (text, image, audio, video, document, etc) |
| `chat_id` | CharField | ID do chat/conversa |
| `contact_number` | CharField | Número do contato |
| `text_content` | TextField | Conteúdo de texto |
| `media_url` | URLField | URL da mídia (quando aplicável) |
| `status` | CharField | Status (queued, sent, delivered, read, failed, error) |
| `queued_at` | DateTime | Data/hora de criação |
| `sent_at` | DateTime | Data/hora de envio |
| `delivered_at` | DateTime | Data/hora de entrega |
| `read_at` | DateTime | Data/hora de leitura |

#### Propriedades de Latência

- `latency_to_sent_ms`: Latência desde criação até envio (ms)
- `latency_to_delivered_ms`: Latência desde criação até entrega (ms)
- `latency_to_read_ms`: Latência desde criação até leitura (ms)
- `total_latency_ms`: Latência total até status mais recente (ms)
- `is_latency_acceptable`: `True` se latência < 5000ms (5 segundos)

#### Métodos

- `mark_as_sent()`: Marca mensagem como enviada
- `mark_as_delivered()`: Marca mensagem como entregue
- `mark_as_read()`: Marca mensagem como lida
- `mark_as_error(error_msg)`: Marca mensagem com erro

---

## 🔌 Endpoints API

Base URL: `/api/v1/whatsapp/`

### Sessões

#### Listar Sessões
```http
GET /api/v1/whatsapp/sessions/
```

**Query Parameters:**
- `status`: Filtrar por status (disconnected, connecting, qrcode, ready, error)
- `is_active`: Filtrar sessões ativas (true/false)
- `search`: Buscar por número de telefone ou nome do dispositivo

**Response:**
```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "usuario": 1,
      "usuario_nome": "admin",
      "status": "ready",
      "phone_number": "5511999999999",
      "is_connected": true,
      "total_messages_sent": 150,
      "total_messages_received": 230,
      "last_message_at": "2025-10-11T10:30:00Z",
      "updated_at": "2025-10-11T10:30:00Z"
    }
  ]
}
```

---

#### Iniciar Sessão
```http
POST /api/v1/whatsapp/sessions/start/
```

**Response:**
```json
{
  "session_id": 1,
  "status": "connecting",
  "message": "Sessão iniciada com sucesso"
}
```

**Status Codes:**
- `202 Accepted`: Sessão iniciada
- `500 Internal Server Error`: Erro ao iniciar

---

#### Parar Sessão
```http
POST /api/v1/whatsapp/sessions/stop/
```

**Response:**
```json
{
  "message": "Sessão encerrada com sucesso"
}
```

---

#### Status da Sessão
```http
GET /api/v1/whatsapp/sessions/status/
```

**Response:**
```json
{
  "session_id": 1,
  "status": "ready",
  "is_connected": true,
  "phone_number": "5511999999999",
  "device_name": "DX Connect Web",
  "connected_at": "2025-10-11T08:00:00Z",
  "uptime_seconds": 9000,
  "total_messages_sent": 150,
  "total_messages_received": 230,
  "last_message_at": "2025-10-11T10:30:00Z",
  "error_count": 0
}
```

---

#### Métricas da Sessão
```http
GET /api/v1/whatsapp/sessions/{id}/metrics/
```

**Response:**
```json
{
  "session_id": 1,
  "total_messages": 380,
  "messages_sent": 150,
  "messages_received": 230,
  "messages_with_error": 2,
  "avg_latency_ms": 1250.5,
  "latency_acceptable_rate": 98.5,
  "uptime_seconds": 9000,
  "error_count": 0
}
```

---

### Mensagens

#### Listar Mensagens
```http
GET /api/v1/whatsapp/messages/
```

**Query Parameters:**
- `direction`: Filtrar por direção (inbound/outbound)
- `message_type`: Filtrar por tipo (text, image, audio, etc)
- `status`: Filtrar por status (queued, sent, delivered, read, error)
- `chat_id`: Filtrar por chat
- `session`: Filtrar por sessão
- `search`: Buscar em conteúdo, número ou nome do contato

**Response:**
```json
{
  "count": 380,
  "results": [
    {
      "id": 1,
      "message_id": "msg_abc123",
      "direction": "outbound",
      "message_type": "text",
      "contact_number": "5511988888888",
      "text_content": "Olá! Como posso ajudar?",
      "status": "read",
      "created_at": "2025-10-11T10:00:00Z",
      "total_latency_ms": 1230,
      "is_latency_acceptable": true
    }
  ]
}
```

---

#### Detalhar Mensagem
```http
GET /api/v1/whatsapp/messages/{id}/
```

**Response:**
```json
{
  "id": 1,
  "session": 1,
  "usuario": 1,
  "usuario_nome": "admin",
  "message_id": "msg_abc123",
  "client_message_id": "",
  "direction": "outbound",
  "message_type": "text",
  "chat_id": "5511988888888",
  "contact_number": "5511988888888",
  "contact_name": "João Silva",
  "text_content": "Olá! Como posso ajudar?",
  "media_url": "",
  "status": "read",
  "created_at": "2025-10-11T10:00:00Z",
  "queued_at": "2025-10-11T10:00:00Z",
  "sent_at": "2025-10-11T10:00:01.230Z",
  "delivered_at": "2025-10-11T10:00:02.450Z",
  "read_at": "2025-10-11T10:00:05.120Z",
  "latency_to_sent_ms": 1230,
  "latency_to_delivered_ms": 2450,
  "latency_to_read_ms": 5120,
  "total_latency_ms": 5120,
  "is_latency_acceptable": false
}
```

---

#### Enviar Mensagem
```http
POST /api/v1/whatsapp/send/
```

**Request Body (Texto):**
```json
{
  "to": "5511988888888",
  "type": "text",
  "text": "Olá! Como posso ajudar?",
  "client_message_id": "my-custom-id-123"
}
```

**Request Body (Imagem):**
```json
{
  "to": "5511988888888",
  "type": "image",
  "media_url": "https://example.com/image.jpg",
  "text": "Legenda da imagem"
}
```

**Response:**
```json
{
  "message_id": "msg_xyz789",
  "database_id": 381,
  "status": "queued",
  "message": "Mensagem enfileirada para envio"
}
```

**Status Codes:**
- `202 Accepted`: Mensagem enfileirada
- `400 Bad Request`: Dados inválidos
- `423 Locked`: Sessão não está pronta
- `500 Internal Server Error`: Erro ao enviar

---

#### Mensagens com Alta Latência
```http
GET /api/v1/whatsapp/messages/high-latency/
```

Lista mensagens que excederam o limite de 5 segundos.

**Response:**
```json
[
  {
    "id": 1,
    "message_id": "msg_slow",
    "direction": "outbound",
    "message_type": "text",
    "contact_number": "5511999999999",
    "text_content": "Mensagem lenta",
    "status": "sent",
    "created_at": "2025-10-11T10:00:00Z",
    "total_latency_ms": 7230,
    "is_latency_acceptable": false
  }
]
```

---

#### Estatísticas de Latência
```http
GET /api/v1/whatsapp/messages/latency-stats/
```

**Response:**
```json
{
  "total_messages": 380,
  "outbound_messages": 150,
  "inbound_messages": 230,
  "avg_latency_to_sent_ms": 1250.5,
  "avg_latency_to_delivered_ms": 2180.3,
  "messages_over_5s": 3,
  "latency_acceptable_rate": 98.0
}
```

---

## 🔌 WebSocket

### Conexão

```javascript
const token = 'your-jwt-token';
const ws = new WebSocket(`ws://localhost:8001/ws/whatsapp/?token=${token}`);
```

### Eventos Recebidos

#### 1. Status da Sessão
```json
{
  "type": "session_status",
  "status": "ready",
  "ts": "2025-10-11T10:00:00Z"
}
```

**Status Possíveis:**
- `disconnected`: Desconectado
- `connecting`: Conectando
- `qrcode`: Aguardando leitura do QR Code
- `authenticated`: Autenticado
- `ready`: Pronto para enviar/receber mensagens
- `error`: Erro

---

#### 2. QR Code
```json
{
  "type": "qrcode",
  "image_b64": "base64-encoded-qr-code",
  "ts": "2025-10-11T10:00:05Z"
}
```

---

#### 3. Mensagem Recebida
```json
{
  "type": "message_received",
  "message_id": "msg_abc123",
  "from": "5511988888888",
  "chat_id": "5511988888888",
  "payload": {
    "type": "text",
    "text": "Olá! Preciso de ajuda",
    "contact_name": "João Silva"
  },
  "ts": "2025-10-11T10:15:00Z"
}
```

---

#### 4. Status da Mensagem
```json
{
  "type": "message_status",
  "message_id": "msg_xyz789",
  "status": "delivered",
  "ts": "2025-10-11T10:00:02.450Z"
}
```

**Status Possíveis:**
- `queued`: Na fila
- `sent`: Enviada
- `delivered`: Entregue
- `read`: Lida

---

### Ping/Pong

Para manter a conexão ativa:

**Enviar:**
```json
{
  "type": "ping"
}
```

**Receber:**
```json
{
  "type": "pong"
}
```

---

## 📈 Métricas de Latência

### Critérios de Aceitação

✅ **Latência Aceitável**: < 5 segundos (5000ms)  
❌ **Latência Alta**: ≥ 5 segundos

### Cálculos

1. **Latência de Envio**: `sent_at - queued_at`
2. **Latência de Entrega**: `delivered_at - queued_at`
3. **Latência de Leitura**: `read_at - queued_at`
4. **Latência Total**: Até o status mais recente

### Logs

O sistema registra automaticamente:
- ✅ Mensagens com latência aceitável (nível INFO)
- ⚠️ Mensagens com latência alta (nível WARNING)

---

## 💡 Exemplos de Uso

### Python (Requests)

#### Iniciar Sessão
```python
import requests

url = 'http://localhost:8001/api/v1/whatsapp/sessions/start/'
headers = {
    'Authorization': 'Bearer your-jwt-token',
    'Content-Type': 'application/json'
}

response = requests.post(url, headers=headers)
print(response.json())
# {'session_id': 1, 'status': 'connecting', 'message': 'Sessão iniciada com sucesso'}
```

#### Enviar Mensagem
```python
import requests

url = 'http://localhost:8001/api/v1/whatsapp/send/'
headers = {
    'Authorization': 'Bearer your-jwt-token',
    'Content-Type': 'application/json'
}
data = {
    'to': '5511988888888',
    'type': 'text',
    'text': 'Olá! Como posso ajudar?'
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
# {'message_id': 'msg_xyz789', 'database_id': 1, 'status': 'queued'}
```

---

### JavaScript (Fetch)

#### Obter Status da Sessão
```javascript
const token = 'your-jwt-token';

fetch('http://localhost:8001/api/v1/whatsapp/sessions/status/', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(res => res.json())
.then(data => console.log(data));
// {session_id: 1, status: "ready", is_connected: true, ...}
```

#### WebSocket (Eventos)
```javascript
const token = 'your-jwt-token';
const ws = new WebSocket(`ws://localhost:8001/ws/whatsapp/?token=${token}`);

ws.onopen = () => {
  console.log('Conectado ao WebSocket');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Evento recebido:', data);
  
  if (data.type === 'qrcode') {
    // Exibir QR Code
    console.log('QR Code:', data.image_b64);
  } else if (data.type === 'message_received') {
    // Processar mensagem recebida
    console.log('Nova mensagem:', data.payload.text);
  }
};
```

---

## 🧪 Testes

### Executar Testes

```bash
# Todos os testes do app whatsapp
docker-compose exec web python manage.py test whatsapp

# Testes específicos
docker-compose exec web python manage.py test whatsapp.tests.test_models
docker-compose exec web python manage.py test whatsapp.tests.test_views
docker-compose exec web python manage.py test whatsapp.tests.test_integration
```

### Cobertura de Testes

- ✅ **Modelos**: CRUD, propriedades, métodos
- ✅ **Views**: Endpoints, filtros, autenticação
- ✅ **Serviços**: Gestão de sessões, envio/recebimento de mensagens
- ✅ **Integração**: Ciclo completo de sessão e mensagens
- ✅ **Métricas**: Cálculo de latência

---

## 📚 Referências

- **Issue**: #36 - WhatsApp Web - sessão e eventos (latência < 5s)
- **Sprint**: 3 - Atendimento via Chat
- **Modelos**: `whatsapp/models.py`
- **Serviço**: `whatsapp/service.py`
- **Views**: `whatsapp/views.py`
- **WebSocket**: `whatsapp/consumers.py`
- **Testes**: `whatsapp/tests/`

---

## 🔄 Próximos Passos

1. **Issue #44**: WhatsApp: Recebimento de Mensagens (webhook)
2. **Issue #45**: WhatsApp: Envio de Mensagens (fila)
3. **Issue #46**: WhatsApp: Processamento de Mídias
4. **Issue #47**: WhatsApp: Gestão de Sessões e Conexão (completo)

