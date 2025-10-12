# 🚀 Guia Rápido para Frontend - DX Connect

## 📋 Índice

1. [Setup Inicial](#setup-inicial)
2. [Autenticação](#autenticação)
3. [WebSocket](#websocket)
4. [Fluxos Principais](#fluxos-principais)
5. [Exemplos de Código](#exemplos-de-código)

---

## 🔧 Setup Inicial

### Base URL
```javascript
const API_BASE_URL = 'http://localhost:8001/api/v1';
const WS_BASE_URL = 'ws://localhost:8001/ws';
```

### Headers Padrão
```javascript
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${token}`
};
```

---

## 🔐 Autenticação

### 1. Login
```javascript
async function login(username, password) {
  const response = await fetch(`${API_BASE_URL}/auth/token/`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username, password})
  });
  
  const data = await response.json();
  
  // Salvar tokens
  localStorage.setItem('access_token', data.access);
  localStorage.setItem('refresh_token', data.refresh);
  
  return data;
}
```

### 2. Refresh Token
```javascript
async function refreshToken() {
  const refresh = localStorage.getItem('refresh_token');
  
  const response = await fetch(`${API_BASE_URL}/auth/refresh/`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({refresh})
  });
  
  const data = await response.json();
  localStorage.setItem('access_token', data.access);
  
  return data.access;
}
```

### 3. Interceptor para Token Expirado
```javascript
async function apiCall(url, options = {}) {
  let token = localStorage.getItem('access_token');
  
  options.headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`
  };
  
  let response = await fetch(url, options);
  
  // Se token expirou, refresh e tenta novamente
  if (response.status === 401) {
    token = await refreshToken();
    options.headers['Authorization'] = `Bearer ${token}`;
    response = await fetch(url, options);
  }
  
  return response;
}
```

---

## 🔌 WebSocket

### 1. Conectar WebSocket
```javascript
class WhatsAppWebSocket {
  constructor(token) {
    this.token = token;
    this.ws = null;
    this.reconnectInterval = null;
    this.handlers = {};
  }
  
  connect() {
    this.ws = new WebSocket(`${WS_BASE_URL}/whatsapp/?token=${this.token}`);
    
    this.ws.onopen = () => {
      console.log('WebSocket conectado');
      this.startHeartbeat();
    };
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleEvent(data);
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket desconectado, reconectando...');
      this.reconnect();
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }
  
  startHeartbeat() {
    // Ping a cada 30s
    setInterval(() => {
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({type: 'ping'}));
      }
    }, 30000);
  }
  
  reconnect() {
    setTimeout(() => this.connect(), 3000);
  }
  
  handleEvent(data) {
    const handler = this.handlers[data.event];
    if (handler) {
      handler(data.data);
    }
  }
  
  on(event, callback) {
    this.handlers[event] = callback;
  }
  
  send(data) {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
}

// Uso
const ws = new WhatsAppWebSocket(token);
ws.connect();

ws.on('message_received', (data) => {
  console.log('Nova mensagem:', data);
  playSound('new_message.mp3');
  addMessageToChat(data);
});

ws.on('chat_assigned', (data) => {
  console.log('Novo atendimento:', data);
  playSound('new_chat.mp3');
  showNotification('Novo atendimento', data.cliente_nome);
  addNewChatToList(data);
});
```

---

## 🔄 Fluxos Principais

### Fluxo 1: Iniciar WhatsApp e Receber Mensagens

```javascript
// 1. Iniciar sessão WhatsApp
async function iniciarWhatsApp() {
  const response = await apiCall(`${API_BASE_URL}/whatsapp/sessions/start/`, {
    method: 'POST'
  });
  const data = await response.json();
  console.log('Sessão iniciada:', data);
}

// 2. Conectar WebSocket
const ws = new WhatsAppWebSocket(token);
ws.connect();

// 3. Listener para QR Code
ws.on('qrcode', (data) => {
  const qrImage = `data:image/png;base64,${data.image_b64}`;
  document.getElementById('qr-code').src = qrImage;
});

// 4. Listener para status
ws.on('session_status', (data) => {
  updateSessionStatus(data.status); // connecting, qrcode, ready
});

// 5. Listener para mensagens
ws.on('message_received', (data) => {
  addMessageToChat({
    from: data.from,
    text: data.message,
    timestamp: data.timestamp,
    isFromMe: false
  });
  
  playNotificationSound();
});
```

---

### Fluxo 2: Enviar Mensagem

```javascript
async function enviarMensagem(to, text) {
  const response = await apiCall(`${API_BASE_URL}/whatsapp/send/`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      to: to,
      type: 'text',
      text: text
    })
  });
  
  const data = await response.json();
  
  // Adiciona mensagem otimisticamente
  addMessageToChat({
    to: to,
    text: text,
    timestamp: new Date().toISOString(),
    isFromMe: true,
    status: 'queued'
  });
  
  return data;
}

// Listener para confirmação
ws.on('message_sent', (data) => {
  updateMessageStatus(data.message_id, data.status);
});
```

---

### Fluxo 3: Atendimento

```javascript
// 1. Buscar meus atendimentos ativos
async function buscarMeusAtendimentos() {
  const response = await apiCall(
    `${API_BASE_URL}/atendimento/atendimentos/meus-atendimentos/`
  );
  return await response.json();
}

// 2. Listener para novo atendimento
ws.on('chat_assigned', (data) => {
  showNotification('Novo Atendimento', data.cliente_nome);
  
  const newChat = {
    id: data.atendimento_id,
    cliente: data.cliente_nome,
    chatId: data.chat_id,
    prioridade: data.prioridade,
    mensagemInicial: data.mensagem_inicial
  };
  
  addChatToList(newChat);
});

// 3. Transferir atendimento
async function transferirAtendimento(atendimentoId, atendenteDestinoId, motivo) {
  const response = await apiCall(
    `${API_BASE_URL}/atendimento/atendimentos/${atendimentoId}/transferir/`,
    {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        atendente_destino_id: atendenteDestinoId,
        motivo: motivo
      })
    }
  );
  
  return await response.json();
}

// 4. Finalizar atendimento
async function finalizarAtendimento(atendimentoId, observacoes) {
  const response = await apiCall(
    `${API_BASE_URL}/atendimento/atendimentos/${atendimentoId}/finalizar/`,
    {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({observacoes})
    }
  );
  
  return await response.json();
}
```

---

### Fluxo 4: Presença e Digitação

```javascript
// 1. Alterar status
async function setStatus(status, message = '') {
  await apiCall(`${API_BASE_URL}/presence/set-status/`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({status, message})
  });
}

// 2. Heartbeat automático
setInterval(async () => {
  await apiCall(`${API_BASE_URL}/presence/heartbeat/`, {
    method: 'POST'
  });
}, 30000); // A cada 30s

// 3. Indicador de digitação
let typingTimeout;

function onTyping(chatId) {
  // Enviar typing_start
  apiCall(`${API_BASE_URL}/typing/`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({chat_id: chatId})
  });
  
  // Auto-parar após 3s sem digitação
  clearTimeout(typingTimeout);
  typingTimeout = setTimeout(() => {
    stopTyping(chatId);
  }, 3000);
}

function stopTyping(chatId) {
  apiCall(`${API_BASE_URL}/typing/?chat_id=${chatId}`, {
    method: 'DELETE'
  });
}

// Uso no input
document.getElementById('message-input').addEventListener('keypress', () => {
  const chatId = getCurrentChatId();
  onTyping(chatId);
});
```

---

## 🎨 Componentes Recomendados

### Estrutura de Pastas
```
src/
├── services/
│   ├── api.js              # Cliente HTTP com interceptors
│   ├── websocket.js        # Cliente WebSocket
│   ├── auth.js             # Autenticação
│   └── whatsapp.js         # Específico do WhatsApp
├── components/
│   ├── Chat/
│   │   ├── ChatList.jsx    # Lista de conversas
│   │   ├── ChatWindow.jsx  # Janela de mensagens
│   │   └── MessageInput.jsx
│   ├── WhatsApp/
│   │   ├── QRCode.jsx
│   │   └── SessionStatus.jsx
│   └── Notifications/
│       ├── ToastNotification.jsx
│       └── DesktopNotification.js
└── hooks/
    ├── useWebSocket.js
    ├── useWhatsApp.js
    └── usePresence.js
```

---

## ⚡ Dicas de Performance

### 1. Debounce na Digitação
```javascript
const debounce = (func, wait) => {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
};

const debouncedTyping = debounce((chatId) => onTyping(chatId), 300);
```

### 2. Cache de Mensagens
```javascript
// Usar React Query, SWR ou similar
const { data, isLoading } = useQuery(
  ['messages', chatId],
  () => fetchMessages(chatId),
  {
    staleTime: 30000, // 30s
    cacheTime: 300000 // 5min
  }
);
```

### 3. Virtual Scroll para Listas
Use `react-window` ou `react-virtualized` para listas longas de mensagens/chats.

---

## 🔔 Sistema de Notificações

### Desktop Notifications
```javascript
// Pedir permissão
Notification.requestPermission();

// Mostrar notificação
function showDesktopNotification(title, body) {
  if (Notification.permission === 'granted') {
    new Notification(title, {
      body: body,
      icon: '/logo.png',
      badge: '/badge.png',
      tag: 'dx-connect',
      requireInteraction: false
    });
  }
}
```

### Sons
```javascript
const sounds = {
  newMessage: new Audio('/sounds/new_message.mp3'),
  newChat: new Audio('/sounds/new_chat.mp3'),
  transfer: new Audio('/sounds/transfer.mp3')
};

function playSound(type) {
  const sound = sounds[type];
  if (sound) {
    sound.play().catch(err => console.log('Autoplay bloqueado'));
  }
}
```

---

## 📱 Estados da Aplicação

### Estados do WhatsApp
```javascript
const SESSION_STATUS = {
  DISCONNECTED: 'disconnected',
  CONNECTING: 'connecting',
  QRCODE: 'qrcode',
  AUTHENTICATED: 'authenticated',
  READY: 'ready',
  ERROR: 'error'
};
```

### Estados do Atendimento
```javascript
const ATENDIMENTO_STATUS = {
  AGUARDANDO: 'aguardando',
  EM_ATENDIMENTO: 'em_atendimento',
  PAUSADO: 'pausado',
  FINALIZADO: 'finalizado',
  CANCELADO: 'cancelado'
};
```

### Status de Presença
```javascript
const PRESENCE_STATUS = {
  ONLINE: 'online',
  OFFLINE: 'offline',
  BUSY: 'busy',
  AWAY: 'away'
};
```

---

## ✅ Checklist de Implementação

### Obrigatório
- [ ] Autenticação JWT
- [ ] WebSocket conectado
- [ ] Heartbeat a cada 30s
- [ ] Tratamento de reconexão WS
- [ ] Listeners de eventos principais
- [ ] Notificações desktop
- [ ] Sons de alerta

### Recomendado
- [ ] Modo não perturbe
- [ ] Indicadores de digitação
- [ ] Cache de mensagens
- [ ] Virtual scroll
- [ ] Otimistic updates
- [ ] Error boundaries
- [ ] Loading states
- [ ] Empty states

---

## 🎯 Telas Principais

### 1. Login
- Input username/password
- Botão entrar
- Link esqueci senha

### 2. Dashboard
- Lista de atendimentos ativos
- Contadores (mensagens, atendimentos, fila)
- Status de presença
- Botão iniciar WhatsApp

### 3. WhatsApp Setup
- QR Code (quando status = 'qrcode')
- Status da conexão
- Botão reconectar

### 4. Chat
- Lista de conversas (esquerda)
- Janela de mensagens (centro)
- Informações do cliente (direita)
- Input de mensagem
- Indicador de digitação
- Badge de não lidas

### 5. Configurações
- Preferências de notificação
- Status de presença
- Dados da empresa
- Templates de documentos

---

## 🚨 Tratamento de Erros

```javascript
async function handleApiError(response) {
  if (!response.ok) {
    const error = await response.json();
    
    switch(response.status) {
      case 400:
        showValidationErrors(error);
        break;
      case 401:
        redirectToLogin();
        break;
      case 403:
        showError('Sem permissão para esta ação');
        break;
      case 404:
        showError('Recurso não encontrado');
        break;
      case 423:
        showError('Sessão WhatsApp não está pronta');
        break;
      case 500:
        showError('Erro no servidor. Tente novamente.');
        break;
      default:
        showError(error.error || 'Erro desconhecido');
    }
    
    throw new Error(error.error || 'API Error');
  }
  
  return response.json();
}
```

---

## 📚 Referências Completas

- **[API Reference](./API_REFERENCE.md)** - Todos os endpoints
- **[WebSocket Events](./NOTIFICATION_EVENTS.md)** - Eventos em tempo real
- **[WhatsApp Guide](./WHATSAPP_SESSION_EVENTS.md)** - Sistema WhatsApp
- **[CORS Configuration](./CORS_CONFIGURATION.md)** - Configuração CORS

---

## 💡 Dicas Finais

1. **Sempre use HTTPS em produção**
2. **Valide dados antes de enviar**
3. **Implemente debounce em buscas**
4. **Use loading states**
5. **Trate erros graciosamente**
6. **Teste em diferentes navegadores**
7. **Implemente modo offline**
8. **Monitore performance**

---

## 🆘 Suporte

**Swagger UI**: http://localhost:8001/api/docs/  
**Backend Logs**: `docker-compose logs -f web`

---

**Boa sorte com o frontend!** 🚀

