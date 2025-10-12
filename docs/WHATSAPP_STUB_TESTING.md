# 🧪 Guia de Testes com WhatsApp Stub

## 📋 Índice
- [Visão Geral](#visão-geral)
- [O que é o Stub?](#o-que-é-o-stub)
- [Cenário: Chat de Suporte](#cenário-chat-de-suporte)
- [Passo a Passo Completo](#passo-a-passo-completo)
- [Exemplos de Código Frontend](#exemplos-de-código-frontend)
- [Simulando Mensagens do Cliente](#simulando-mensagens-do-cliente)
- [Fluxo Completo de Interação](#fluxo-completo-de-interação)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

Este guia explica como testar a funcionalidade de chat de suporte no frontend usando o **WhatsApp Stub** do backend. O stub simula completamente o comportamento do WhatsApp Web sem precisar de uma conta real ou conexão com os servidores do WhatsApp.

---

## 🤖 O que é o Stub?

O **Stub do WhatsApp** (`integrations/whatsapp_stub.py`) é um serviço mock que:

✅ **Simula** todos os estados de conexão WhatsApp
✅ **Emite** eventos em tempo real via WebSocket
✅ **Persiste** mensagens no banco de dados
✅ **Permite** injetar mensagens de entrada para testes
✅ **Funciona** sem conexão externa real

### Estados Simulados

```
disconnected → connecting → qrcode → authenticated → ready
```

- **disconnected**: Sem conexão
- **connecting**: Iniciando conexão
- **qrcode**: QR Code disponível para "leitura" (simulado)
- **authenticated**: Autenticado (após "ler" QR Code)
- **ready**: Pronto para enviar/receber mensagens

---

## 💬 Cenário: Chat de Suporte

### Objetivo
Simular um **cliente iniciando um chat de suporte** e um **atendente respondendo**.

### Atores
1. **Cliente**: Envia mensagem "Olá, preciso de ajuda"
2. **Atendente** (você no frontend): Recebe a mensagem e responde

---

## 📝 Passo a Passo Completo

### 1️⃣ Autenticar no Backend

Primeiro, faça login para obter o token JWT:

```bash
POST http://localhost:8001/api/v1/auth/token/
Content-Type: application/json

{
  "username": "admin",
  "password": "sua_senha"
}
```

**Resposta:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

💾 **Salve o token `access`** para usar nas próximas requisições.

---

### 2️⃣ Conectar ao WebSocket

Estabeleça conexão WebSocket para receber eventos em tempo real:

```javascript
const token = 'seu_token_jwt_aqui';
const ws = new WebSocket(`ws://localhost:8001/ws/whatsapp/?token=${token}`);

ws.onopen = () => {
  console.log('✅ Conectado ao WebSocket WhatsApp');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('📩 Evento recebido:', data);
  
  // Processar eventos (detalhes abaixo)
  handleWhatsAppEvent(data);
};

ws.onerror = (error) => {
  console.error('❌ Erro WebSocket:', error);
};
```

---

### 3️⃣ Iniciar Sessão WhatsApp

Inicie a sessão para "conectar" ao WhatsApp (simulado):

```javascript
async function startWhatsAppSession() {
  const response = await fetch('http://localhost:8001/api/v1/whatsapp/sessions/start/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  const data = await response.json();
  console.log('🚀 Sessão iniciada:', data);
  // { session_id: 1, status: "connecting", message: "Sessão iniciada com sucesso" }
}

startWhatsAppSession();
```

---

### 4️⃣ Aguardar Eventos de Conexão

O stub enviará automaticamente os eventos de conexão via WebSocket:

```javascript
function handleWhatsAppEvent(data) {
  switch(data.type) {
    case 'session_status':
      console.log(`📊 Status: ${data.status}`);
      
      if (data.status === 'qrcode') {
        console.log('📱 Aguardando QR Code...');
      } else if (data.status === 'ready') {
        console.log('✅ Sessão pronta! Pode enviar/receber mensagens.');
        // Sessão pronta para uso
        onSessionReady();
      }
      break;
      
    case 'qrcode':
      console.log('🔲 QR Code disponível (base64):', data.image_b64);
      // Você pode exibir o QR Code na tela (mas é apenas simulação)
      displayQRCode(data.image_b64);
      break;
      
    case 'message_received':
      console.log('📨 Nova mensagem recebida!');
      handleIncomingMessage(data);
      break;
      
    case 'message_status':
      console.log(`📮 Status da mensagem ${data.message_id}: ${data.status}`);
      updateMessageStatus(data.message_id, data.status);
      break;
  }
}
```

**Sequência de eventos que você receberá:**

```
1. { type: "session_status", status: "connecting" }
2. { type: "session_status", status: "qrcode" }
3. { type: "qrcode", image_b64: "..." }
4. { type: "session_status", status: "authenticated" }
5. { type: "session_status", status: "ready" }  ← PRONTO!
```

⏱️ Por padrão, essa sequência leva **~300ms** (100ms entre cada transição).

---

### 5️⃣ Simular Cliente Enviando Mensagem

Agora que a sessão está `ready`, você pode **injetar uma mensagem de entrada** simulando um cliente.

Existem **2 formas** de fazer isso:

#### Opção A: Via API REST (✅ **Recomendado - Mais Simples**)

```javascript
async function injectCustomerMessage() {
  const response = await fetch('http://localhost:8001/api/v1/whatsapp/inject-incoming/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      from: "5511999887766",
      payload: {
        type: "text",
        text: "Olá, preciso de ajuda com meu pedido!",
        contact_name: "João Silva"
      }
    })
  });
  
  const data = await response.json();
  console.log('✅ Mensagem injetada:', data);
  // {
  //   message: "Mensagem de teste injetada com sucesso",
  //   message_id: "msg_abc123",
  //   database_id: 42,
  //   data: { ... } // Objeto completo da mensagem
  // }
}
```

**Vantagens:**
- ✅ Não precisa de WebSocket aberto
- ✅ Mais fácil para testes automatizados
- ✅ Funciona com Postman/Insomnia
- ✅ Retorna confirmação imediata

#### Opção B: Via WebSocket

```javascript
// Enviar mensagem simulada do cliente via WebSocket
function simulateCustomerMessage() {
  const incomingMessage = {
    type: "inject_incoming",
    from: "5511999887766",  // Número do "cliente"
    chat_id: "5511999887766",
    payload: {
      type: "text",
      text: "Olá, preciso de ajuda com meu pedido!",
      contact_name: "João Silva"
    }
  };
  
  ws.send(JSON.stringify(incomingMessage));
  console.log('📤 Mensagem do cliente simulada enviada');
}

// Chamar quando sessão estiver ready
function onSessionReady() {
  console.log('✅ Sessão pronta! Simulando mensagem de cliente...');
  
  // Aguardar 1 segundo e simular mensagem
  setTimeout(() => {
    simulateCustomerMessage();
  }, 1000);
}
```

**Vantagens:**
- ✅ Tempo real
- ✅ Recebe confirmação via WS (`inject_success` ou `inject_error`)

---

### 6️⃣ Receber Mensagem do Cliente

Quando você injetar a mensagem, receberá via WebSocket:

```javascript
function handleIncomingMessage(data) {
  console.log('📨 NOVA MENSAGEM RECEBIDA!');
  console.log('De:', data.from);              // "5511999887766"
  console.log('Chat:', data.chat_id);         // "5511999887766"
  console.log('Texto:', data.payload.text);   // "Olá, preciso de ajuda com meu pedido!"
  console.log('Nome:', data.payload.contact_name); // "João Silva"
  
  // Exibir na interface do chat
  displayMessageInChat({
    id: data.message_id,
    from: data.payload.contact_name || data.from,
    text: data.payload.text,
    direction: 'incoming',
    timestamp: new Date()
  });
  
  // Tocar notificação sonora
  playNotificationSound();
}
```

**Exemplo de evento recebido:**

```json
{
  "type": "message_received",
  "message_id": "msg_1697123456789",
  "from": "5511999887766",
  "chat_id": "5511999887766",
  "payload": {
    "type": "text",
    "text": "Olá, preciso de ajuda com meu pedido!",
    "contact_name": "João Silva"
  },
  "ts": "2025-10-12T10:30:00Z"
}
```

---

### 7️⃣ Responder Mensagem (Atendente)

Agora você (como atendente) pode responder ao cliente:

```javascript
async function sendReplyToCustomer(to, text) {
  const response = await fetch('http://localhost:8001/api/v1/whatsapp/send/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      to: to,  // "5511999887766"
      type: "text",
      text: text,  // "Olá João! Como posso ajudá-lo?"
      client_message_id: `my_msg_${Date.now()}`  // ID opcional para rastrear
    })
  });
  
  const data = await response.json();
  console.log('✅ Resposta enviada:', data);
  
  // Exibir na interface
  displayMessageInChat({
    id: data.message_id,
    text: text,
    direction: 'outgoing',
    status: 'queued',
    timestamp: new Date()
  });
  
  return data.message_id;
}

// Exemplo de uso
sendReplyToCustomer("5511999887766", "Olá João! Como posso ajudá-lo?");
```

**Resposta da API:**

```json
{
  "message_id": "msg_xyz789",
  "database_id": 42,
  "status": "queued",
  "message": "Mensagem enfileirada para envio"
}
```

---

### 8️⃣ Acompanhar Status da Mensagem

Após enviar, você receberá **4 eventos de status** via WebSocket:

```javascript
function updateMessageStatus(messageId, newStatus) {
  console.log(`📮 Mensagem ${messageId} → ${newStatus}`);
  
  // Atualizar UI da mensagem
  const messageElement = document.getElementById(`msg-${messageId}`);
  if (messageElement) {
    messageElement.classList.remove('queued', 'sent', 'delivered', 'read');
    messageElement.classList.add(newStatus);
    
    // Atualizar ícone de status
    updateStatusIcon(messageElement, newStatus);
  }
}

function updateStatusIcon(element, status) {
  const iconMap = {
    'queued': '⏳',
    'sent': '✓',
    'delivered': '✓✓',
    'read': '✓✓ (azul)'
  };
  
  element.querySelector('.status-icon').textContent = iconMap[status];
}
```

**Eventos recebidos (automaticamente):**

```
📮 message_status → queued      (imediato)
📮 message_status → sent        (~50ms depois)
📮 message_status → delivered   (~100ms depois)
📮 message_status → read        (~150ms depois)
```

---

## 💻 Exemplos de Código Frontend

### Exemplo Completo React/Vue/JS Puro

```javascript
class WhatsAppChatClient {
  constructor(apiUrl, token) {
    this.apiUrl = apiUrl;
    this.token = token;
    this.ws = null;
    this.sessionId = null;
    this.messages = [];
    this.eventHandlers = {};
  }
  
  // Conectar WebSocket
  connect() {
    this.ws = new WebSocket(`ws://${this.apiUrl}/ws/whatsapp/?token=${this.token}`);
    
    this.ws.onopen = () => {
      console.log('✅ WebSocket conectado');
      this.emit('connected');
    };
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleEvent(data);
    };
    
    this.ws.onerror = (error) => {
      console.error('❌ Erro WebSocket:', error);
      this.emit('error', error);
    };
  }
  
  // Iniciar sessão
  async startSession() {
    const response = await fetch(`http://${this.apiUrl}/api/v1/whatsapp/sessions/start/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    this.sessionId = data.session_id;
    this.emit('session_started', data);
    return data;
  }
  
  // Enviar mensagem
  async sendMessage(to, text) {
    const response = await fetch(`http://${this.apiUrl}/api/v1/whatsapp/send/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        to: to,
        type: 'text',
        text: text,
        client_message_id: `msg_${Date.now()}`
      })
    });
    
    const data = await response.json();
    
    // Adicionar à lista local
    this.messages.push({
      id: data.message_id,
      to: to,
      text: text,
      direction: 'outgoing',
      status: 'queued',
      timestamp: new Date()
    });
    
    this.emit('message_sent', data);
    return data;
  }
  
  // Simular mensagem recebida (TESTE)
  simulateIncoming(from, text, contactName = null) {
    const message = {
      type: "inject_incoming",
      from: from,
      chat_id: from,
      payload: {
        type: "text",
        text: text,
        contact_name: contactName || from
      }
    };
    
    this.ws.send(JSON.stringify(message));
  }
  
  // Manipular eventos
  handleEvent(data) {
    switch(data.type) {
      case 'session_status':
        this.emit('session_status', data.status);
        if (data.status === 'ready') {
          this.emit('ready');
        }
        break;
        
      case 'qrcode':
        this.emit('qrcode', data.image_b64);
        break;
        
      case 'message_received':
        this.messages.push({
          id: data.message_id,
          from: data.from,
          text: data.payload.text,
          direction: 'incoming',
          contactName: data.payload.contact_name,
          timestamp: new Date(data.ts)
        });
        this.emit('message_received', data);
        break;
        
      case 'message_status':
        const msg = this.messages.find(m => m.id === data.message_id);
        if (msg) {
          msg.status = data.status;
        }
        this.emit('message_status', { id: data.message_id, status: data.status });
        break;
        
      case 'inject_success':
        console.log('✅ Mensagem teste injetada com sucesso');
        break;
    }
  }
  
  // Sistema de eventos
  on(event, handler) {
    if (!this.eventHandlers[event]) {
      this.eventHandlers[event] = [];
    }
    this.eventHandlers[event].push(handler);
  }
  
  emit(event, data) {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event].forEach(handler => handler(data));
    }
  }
}

// USO
const client = new WhatsAppChatClient('localhost:8001', 'seu_token_jwt');

// Configurar handlers
client.on('connected', () => {
  console.log('Conectado!');
  client.startSession();
});

client.on('ready', () => {
  console.log('Sessão pronta!');
  
  // Simular cliente enviando mensagem após 2 segundos
  setTimeout(() => {
    client.simulateIncoming('5511999887766', 'Olá, preciso de ajuda!', 'João Silva');
  }, 2000);
});

client.on('message_received', (data) => {
  console.log('Nova mensagem:', data);
  
  // Responder automaticamente (teste)
  setTimeout(() => {
    client.sendMessage(data.from, 'Olá! Como posso ajudá-lo?');
  }, 1000);
});

client.on('message_status', (data) => {
  console.log(`Status da mensagem ${data.id}: ${data.status}`);
});

// Conectar
client.connect();
```

---

## 🎭 Simulando Mensagens do Cliente

### Cenários de Teste

#### 1. Cliente Iniciando Conversa

```javascript
// Cliente: "Olá, preciso de ajuda"
client.simulateIncoming('5511999887766', 'Olá, preciso de ajuda!', 'João Silva');

// Aguardar 2 segundos e responder
setTimeout(() => {
  client.sendMessage('5511999887766', 'Olá João! Como posso ajudá-lo?');
}, 2000);
```

#### 2. Múltiplas Mensagens do Cliente

```javascript
// Simular conversa completa
const conversation = [
  { from: '5511999887766', text: 'Olá, preciso de ajuda!', name: 'João Silva' },
  { delay: 2000, reply: 'Olá João! Como posso ajudá-lo?' },
  { from: '5511999887766', text: 'Não consigo acessar meu painel' },
  { delay: 1500, reply: 'Entendo. Vou verificar sua conta. Um momento...' },
  { from: '5511999887766', text: 'Ok, obrigado!' },
];

async function simulateConversation() {
  for (const step of conversation) {
    if (step.from) {
      // Mensagem do cliente
      client.simulateIncoming(step.from, step.text, step.name);
      await sleep(500);
    } else if (step.reply) {
      // Resposta do atendente
      await sleep(step.delay);
      await client.sendMessage('5511999887766', step.reply);
    }
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Executar quando pronto
client.on('ready', () => {
  simulateConversation();
});
```

#### 3. Múltiplos Clientes

```javascript
// Simular 3 clientes diferentes enviando mensagens
const customers = [
  { phone: '5511999887766', name: 'João Silva', message: 'Olá, preciso de suporte' },
  { phone: '5511988776655', name: 'Maria Santos', message: 'Meu sistema está lento' },
  { phone: '5511977665544', name: 'Carlos Oliveira', message: 'Como faço upgrade?' },
];

customers.forEach((customer, index) => {
  setTimeout(() => {
    client.simulateIncoming(customer.phone, customer.message, customer.name);
  }, index * 3000);  // 3 segundos entre cada
});
```

#### 4. Mensagens com Mídia (Simulado)

```javascript
// Simular recebimento de imagem
client.simulateIncoming('5511999887766', '[Imagem]', 'João Silva');

// Ou com payload completo via API
fetch('http://localhost:8001/api/v1/whatsapp/inject-incoming/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    from: "5511999887766",
    payload: {
      type: "image",
      media_url: "https://example.com/image.jpg",
      text: "Olha essa imagem!",
      contact_name: "João Silva",
      mime_type: "image/jpeg",
      media_size: 125000
    }
  })
});
```

---

## 🔄 Fluxo Completo de Interação

### Diagrama de Sequência

```
Frontend                  Backend (Stub)              Database
   |                           |                          |
   |-- POST /start ----------->|                          |
   |                           |-- save session --------->|
   |<-- {status:connecting} ---|                          |
   |                           |                          |
   |<-- WS: connecting --------|                          |
   |<-- WS: qrcode ------------|                          |
   |<-- WS: authenticated -----|                          |
   |<-- WS: ready -------------|                          |
   |                           |                          |
   |-- WS: inject_incoming --->|                          |
   |                           |-- save message --------->|
   |<-- WS: message_received --|                          |
   |                           |                          |
   |-- POST /send ------------>|                          |
   |                           |-- save message --------->|
   |<-- {status:queued} -------|                          |
   |                           |                          |
   |<-- WS: status:queued -----|                          |
   |<-- WS: status:sent -------|-- update status -------->|
   |<-- WS: status:delivered --|-- update status -------->|
   |<-- WS: status:read -------|-- update status -------->|
```

### Timeline Típica

```
T+0ms     → Conectar WebSocket
T+50ms    → POST /start (iniciar sessão)
T+100ms   → WS: connecting
T+200ms   → WS: qrcode
T+300ms   → WS: authenticated
T+400ms   → WS: ready ✅
T+1000ms  → Simular mensagem cliente (inject_incoming)
T+1050ms  → WS: message_received
T+3000ms  → POST /send (responder)
T+3050ms  → WS: message_status → queued
T+3100ms  → WS: message_status → sent
T+3150ms  → WS: message_status → delivered
T+3200ms  → WS: message_status → read
```

---

## 🐛 Troubleshooting

### Problema 1: WebSocket não conecta

**Sintoma:** `WebSocket connection failed`

**Soluções:**
```javascript
// 1. Verificar URL correta
const ws = new WebSocket('ws://localhost:8001/ws/whatsapp/?token=SEU_TOKEN');

// 2. Verificar token válido
console.log('Token:', token);

// 3. Verificar CORS (se frontend em porta diferente)
// Backend já está configurado para aceitar conexões
```

### Problema 2: Mensagens não aparecem

**Sintoma:** `inject_incoming` não retorna mensagem

**Soluções:**
```javascript
// 1. Garantir que sessão está "ready"
client.on('ready', () => {
  // SÓ AQUI você pode enviar/injetar mensagens
  client.simulateIncoming(...);
});

// 2. Verificar estrutura do payload
const correctPayload = {
  type: "inject_incoming",  // ← tipo correto
  from: "5511999999999",
  chat_id: "5511999999999",
  payload: {  // ← payload aninhado
    type: "text",
    text: "Mensagem",
    contact_name: "Nome"
  }
};
```

### Problema 3: Status não atualiza

**Sintoma:** Mensagem fica em "queued" para sempre

**Verificar:**
```javascript
// 1. Listener do WebSocket está ativo?
ws.onmessage = (event) => {
  console.log('Evento:', JSON.parse(event.data));  // ← Verificar aqui
};

// 2. Handler de message_status implementado?
client.on('message_status', (data) => {
  console.log('Status atualizado:', data);
});
```

### Problema 4: Eventos duplicados

**Sintoma:** Recebe 2x cada mensagem

**Solução:**
```javascript
// Não criar múltiplas conexões!
// ERRADO:
setInterval(() => {
  const ws = new WebSocket(...);  // ❌ Nova conexão a cada loop
}, 1000);

// CERTO:
const ws = new WebSocket(...);  // ✅ Uma única conexão
```

---

## 🎯 Checklist de Testes

### Frontend deve suportar:

- [ ] Conectar WebSocket com token JWT
- [ ] Iniciar sessão via API
- [ ] Exibir progresso de conexão (connecting → qrcode → ready)
- [ ] Exibir QR Code (mesmo sendo simulado)
- [ ] Receber mensagens via WebSocket
- [ ] Exibir mensagens recebidas na UI
- [ ] Enviar mensagens via API
- [ ] Atualizar status das mensagens (✓, ✓✓, lido)
- [ ] Tocar notificação sonora ao receber mensagem
- [ ] Mostrar indicador de digitação (se implementado)
- [ ] Listar histórico de mensagens via API
- [ ] Filtrar mensagens por chat
- [ ] Reconectar WebSocket se cair

---

## 📚 Referências

- **Documentação completa**: [`WHATSAPP_SESSION_EVENTS.md`](./WHATSAPP_SESSION_EVENTS.md)
- **API Reference**: [`API_REFERENCE.md`](./API_REFERENCE.md)
- **Código do Stub**: `integrations/whatsapp_stub.py`
- **WebSocket Consumer**: `whatsapp/consumers.py`
- **Serviço**: `whatsapp/service.py`

---

## 🚀 Próximos Passos

Após testar com o stub:

1. ✅ Validar UI/UX do chat
2. ✅ Testar performance com múltiplos clientes
3. ✅ Implementar recursos avançados (digitação, leitura, etc)
4. 🔄 Trocar stub por integração real quando pronto
5. 📊 Monitorar métricas de latência em produção

---

**💡 Dica Final:** O stub está configurado para ser **rápido** em testes. Se quiser simular latência real, configure a variável de ambiente `WHATSAPP_STUB_FAST=0` para ter delays mais realistas entre transições de estado.

