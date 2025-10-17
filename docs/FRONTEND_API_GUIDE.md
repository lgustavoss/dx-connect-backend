# 🎨 Guia da API para Frontend - DX Connect

## 📋 Quick Reference

**Base URL**: `http://localhost:8001`  
**Autenticação**: JWT Bearer Token  
**Formato**: JSON

---

## 🚀 Setup Inicial

### 1. Instalar Cliente HTTP

```bash
npm install axios
# ou
npm install fetch
```

### 2. Configurar Cliente API

```javascript
// api/client.js
import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8001/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para adicionar token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor para refresh token
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(
          'http://localhost:8001/api/v1/auth/refresh/',
          { refresh: refreshToken }
        );
        
        localStorage.setItem('access_token', response.data.access);
        originalRequest.headers.Authorization = `Bearer ${response.data.access}`;
        
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Redirecionar para login
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;
```

---

## 🔐 Autenticação

### Login

```javascript
// services/auth.js
import apiClient from '../api/client';

export const login = async (username, password) => {
  try {
    const response = await axios.post(
      'http://localhost:8001/api/v1/auth/token/',
      { username, password }
    );
    
    localStorage.setItem('access_token', response.data.access);
    localStorage.setItem('refresh_token', response.data.refresh);
    
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Login falhou');
  }
};

export const logout = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  window.location.href = '/login';
};

export const getCurrentUser = async () => {
  const response = await apiClient.get('/me/');
  return response.data;
};
```

### Uso no Componente

```javascript
// LoginForm.jsx
import { useState } from 'react';
import { login } from '../services/auth';

function LoginForm() {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      await login(credentials.username, credentials.password);
      window.location.href = '/dashboard';
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Usuário"
        value={credentials.username}
        onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
      />
      <input
        type="password"
        placeholder="Senha"
        value={credentials.password}
        onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
      />
      {error && <div className="error">{error}</div>}
      <button type="submit" disabled={loading}>
        {loading ? 'Entrando...' : 'Entrar'}
      </button>
    </form>
  );
}
```

---

## 👥 Clientes

### Serviço de Clientes

```javascript
// services/clientes.js
import apiClient from '../api/client';

export const clientesService = {
  // Listar com filtros
  listar: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.search) params.append('search', filters.search);
    if (filters.ordering) params.append('ordering', filters.ordering);
    if (filters.page) params.append('page', filters.page);
    
    const response = await apiClient.get(`/clientes/?${params}`);
    return response.data;
  },
  
  // Buscar por ID
  buscar: async (id) => {
    const response = await apiClient.get(`/clientes/${id}/`);
    return response.data;
  },
  
  // Criar
  criar: async (data) => {
    const response = await apiClient.post('/clientes/', data);
    return response.data;
  },
  
  // Atualizar
  atualizar: async (id, data) => {
    const response = await apiClient.patch(`/clientes/${id}/`, data);
    return response.data;
  },
  
  // Alterar status
  alterarStatus: async (id, status, motivo = '') => {
    const response = await apiClient.patch(`/clientes/${id}/status/`, {
      status,
      motivo
    });
    return response.data;
  },
  
  // Estatísticas
  estatisticas: async () => {
    const response = await apiClient.get('/clientes/stats/');
    return response.data;
  },
  
  // Buscar por CEP
  buscarCEP: async (cep) => {
    const response = await apiClient.get(`/integrations/cep/${cep}/`);
    return response.data;
  }
};
```

### Hook React

```javascript
// hooks/useClientes.js
import { useState, useEffect } from 'react';
import { clientesService } from '../services/clientes';

export function useClientes(filters = {}) {
  const [clientes, setClientes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({ count: 0, next: null, previous: null });
  
  const carregarClientes = async () => {
    try {
      setLoading(true);
      const data = await clientesService.listar(filters);
      setClientes(data.results);
      setPagination({
        count: data.count,
        next: data.next,
        previous: data.previous
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    carregarClientes();
  }, [JSON.stringify(filters)]);
  
  return { clientes, loading, error, pagination, recarregar: carregarClientes };
}
```

### Componente Lista

```javascript
// components/ClientesList.jsx
import { useClientes } from '../hooks/useClientes';
import { useState } from 'react';

function ClientesList() {
  const [filters, setFilters] = useState({ status: 'ativo', page: 1 });
  const { clientes, loading, error, pagination } = useClientes(filters);
  
  if (loading) return <div>Carregando...</div>;
  if (error) return <div>Erro: {error}</div>;
  
  return (
    <div>
      <h1>Clientes ({pagination.count})</h1>
      
      {/* Filtros */}
      <div className="filters">
        <select
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value, page: 1 })}
        >
          <option value="">Todos</option>
          <option value="ativo">Ativos</option>
          <option value="inativo">Inativos</option>
          <option value="suspenso">Suspensos</option>
        </select>
        
        <input
          type="search"
          placeholder="Buscar..."
          onChange={(e) => setFilters({ ...filters, search: e.target.value, page: 1 })}
        />
      </div>
      
      {/* Lista */}
      <table>
        <thead>
          <tr>
            <th>Razão Social</th>
            <th>CNPJ/CPF</th>
            <th>Status</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          {clientes.map((cliente) => (
            <tr key={cliente.id}>
              <td>{cliente.razao_social}</td>
              <td>{cliente.cnpj}</td>
              <td>
                <span className={`badge badge-${cliente.status}`}>
                  {cliente.status}
                </span>
              </td>
              <td>
                <button onClick={() => window.location.href = `/clientes/${cliente.id}`}>
                  Ver
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      
      {/* Paginação */}
      <div className="pagination">
        <button
          disabled={!pagination.previous}
          onClick={() => setFilters({ ...filters, page: filters.page - 1 })}
        >
          Anterior
        </button>
        <span>Página {filters.page}</span>
        <button
          disabled={!pagination.next}
          onClick={() => setFilters({ ...filters, page: filters.page + 1 })}
        >
          Próxima
        </button>
      </div>
    </div>
  );
}
```

---

## 💬 WhatsApp

### Serviço WhatsApp

```javascript
// services/whatsapp.js
import apiClient from '../api/client';

export const whatsappService = {
  // Sessões
  iniciarSessao: async () => {
    const response = await apiClient.post('/whatsapp/sessions/start/');
    return response.data;
  },
  
  pararSessao: async () => {
    const response = await apiClient.post('/whatsapp/sessions/stop/');
    return response.data;
  },
  
  statusSessao: async () => {
    const response = await apiClient.get('/whatsapp/sessions/status/');
    return response.data;
  },
  
  // Mensagens
  enviarMensagem: async (to, text) => {
    const response = await apiClient.post('/whatsapp/send/', {
      to,
      type: 'text',
      text,
      client_message_id: `msg_${Date.now()}`
    });
    return response.data;
  },
  
  listarMensagens: async (filters = {}) => {
    const params = new URLSearchParams(filters);
    const response = await apiClient.get(`/whatsapp/messages/?${params}`);
    return response.data;
  }
};
```

### WebSocket Hook

```javascript
// hooks/useWhatsAppWebSocket.js
import { useEffect, useRef, useState } from 'react';

export function useWhatsAppWebSocket() {
  const ws = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState(null);
  const [sessionStatus, setSessionStatus] = useState('disconnected');
  
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    
    ws.current = new WebSocket(`ws://localhost:8001/ws/whatsapp/?token=${token}`);
    
    ws.current.onopen = () => {
      console.log('WebSocket conectado');
      setIsConnected(true);
      
      // Heartbeat a cada 30s
      const interval = setInterval(() => {
        if (ws.current?.readyState === WebSocket.OPEN) {
          ws.current.send(JSON.stringify({ type: 'ping' }));
        }
      }, 30000);
      
      return () => clearInterval(interval);
    };
    
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setLastEvent(data);
      
      if (data.type === 'session_status') {
        setSessionStatus(data.status);
      }
    };
    
    ws.current.onerror = (error) => {
      console.error('WebSocket erro:', error);
    };
    
    ws.current.onclose = () => {
      console.log('WebSocket desconectado');
      setIsConnected(false);
    };
    
    return () => {
      ws.current?.close();
    };
  }, []);
  
  return {
    isConnected,
    lastEvent,
    sessionStatus,
    simulateIncoming: (from, text) => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send(JSON.stringify({
          type: 'inject_incoming',
          from,
          chat_id: from,
          payload: {
            type: 'text',
            text,
            contact_name: from
          }
        }));
      }
    }
  };
}
```

### Componente Chat

```javascript
// components/ChatWhatsApp.jsx
import { useState, useEffect } from 'react';
import { whatsappService } from '../services/whatsapp';
import { useWhatsAppWebSocket } from '../hooks/useWhatsAppWebSocket';

function ChatWhatsApp() {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [currentChat, setCurrentChat] = useState('5511999999999');
  const { isConnected, lastEvent, sessionStatus } = useWhatsAppWebSocket();
  
  // Processar eventos do WebSocket
  useEffect(() => {
    if (!lastEvent) return;
    
    if (lastEvent.type === 'message_received') {
      setMessages(prev => [...prev, {
        id: lastEvent.message_id,
        from: lastEvent.payload.contact_name || lastEvent.from,
        text: lastEvent.payload.text,
        direction: 'incoming',
        timestamp: new Date()
      }]);
      
      // Tocar som de notificação
      playNotificationSound();
    } else if (lastEvent.type === 'message_status') {
      // Atualizar status da mensagem
      setMessages(prev => prev.map(msg =>
        msg.id === lastEvent.message_id
          ? { ...msg, status: lastEvent.status }
          : msg
      ));
    }
  }, [lastEvent]);
  
  const handleIniciarSessao = async () => {
    try {
      await whatsappService.iniciarSessao();
    } catch (error) {
      alert('Erro ao iniciar sessão: ' + error.message);
    }
  };
  
  const handleEnviarMensagem = async () => {
    if (!inputText.trim()) return;
    
    try {
      const response = await whatsappService.enviarMensagem(currentChat, inputText);
      
      // Adicionar mensagem à lista
      setMessages(prev => [...prev, {
        id: response.message_id,
        text: inputText,
        direction: 'outgoing',
        status: 'queued',
        timestamp: new Date()
      }]);
      
      setInputText('');
    } catch (error) {
      alert('Erro ao enviar: ' + error.message);
    }
  };
  
  const playNotificationSound = () => {
    const audio = new Audio('/sounds/notification.mp3');
    audio.play();
  };
  
  return (
    <div className="chat-container">
      {/* Status da Sessão */}
      <div className="session-status">
        <span className={`status-indicator status-${sessionStatus}`}></span>
        Status: {sessionStatus}
        {!isConnected && <span> (WebSocket desconectado)</span>}
        
        {sessionStatus === 'disconnected' && (
          <button onClick={handleIniciarSessao}>Iniciar Sessão</button>
        )}
      </div>
      
      {/* Mensagens */}
      <div className="messages">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`message message-${msg.direction}`}
          >
            {msg.direction === 'incoming' && (
              <div className="message-from">{msg.from}</div>
            )}
            <div className="message-text">{msg.text}</div>
            <div className="message-meta">
              {msg.timestamp.toLocaleTimeString()}
              {msg.direction === 'outgoing' && (
                <span className={`status-icon status-${msg.status}`}>
                  {msg.status === 'read' && '✓✓'}
                  {msg.status === 'delivered' && '✓✓'}
                  {msg.status === 'sent' && '✓'}
                  {msg.status === 'queued' && '⏳'}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
      
      {/* Input */}
      <div className="input-area">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleEnviarMensagem()}
          placeholder="Digite sua mensagem..."
          disabled={sessionStatus !== 'ready'}
        />
        <button
          onClick={handleEnviarMensagem}
          disabled={sessionStatus !== 'ready' || !inputText.trim()}
        >
          Enviar
        </button>
      </div>
    </div>
  );
}
```

---

## 💬 Chats (Conversas)

### Serviço de Chats

```javascript
// services/chats.js
import apiClient from '../api/client';

export const chatsService = {
  // Listar conversas
  listarChats: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.atendente) params.append('atendente', filters.atendente);
    if (filters.sort) params.append('sort', filters.sort || 'lastMessage');
    if (filters.order) params.append('order', filters.order || 'desc');
    
    const response = await apiClient.get(`/chats/?${params}`);
    return response.data;
  },
  
  // Detalhar conversa
  detalharChat: async (chatId) => {
    const response = await apiClient.get(`/chats/${chatId}/`);
    return response.data;
  },
  
  // Mensagens do chat (histórico isolado)
  mensagensDoChat: async (chatId, limit = 50, offset = 0) => {
    const response = await apiClient.get(
      `/chats/${chatId}/messages/?limit=${limit}&offset=${offset}`
    );
    return response.data;
  },
  
  // Assumir chat (para agentes)
  assumirChat: async (chatId) => {
    const response = await apiClient.post(`/chats/${chatId}/attend/`);
    return response.data;
  },
  
  // Aceitar atendimento
  aceitarChat: async (chatId, observacoes = '') => {
    const response = await apiClient.post(`/chats/${chatId}/aceitar/`, {
      observacoes
    });
    return response.data;
  },
  
  // Transferir chat
  transferirChat: async (chatId, atendenteDestinoId, motivo) => {
    const response = await apiClient.post(`/chats/${chatId}/transferir/`, {
      atendente_destino_id: atendenteDestinoId,
      motivo
    });
    return response.data;
  },
  
  // Encerrar chat
  encerrarChat: async (chatId, observacoes = '', solicitarAvaliacao = true) => {
    const response = await apiClient.post(`/chats/${chatId}/encerrar/`, {
      observacoes,
      solicitar_avaliacao: solicitarAvaliacao
    });
    return response.data;
  }
};
```

### Hook React para Chats

```javascript
// hooks/useChats.js
import { useState, useEffect } from 'react';
import { chatsService } from '../services/chats';

export function useChats(filters = {}) {
  const [chats, setChats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const carregarChats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await chatsService.listarChats(filters);
      setChats(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    carregarChats();
  }, [JSON.stringify(filters)]);
  
  const assumirChat = async (chatId) => {
    try {
      const resultado = await chatsService.assumirChat(chatId);
      await carregarChats(); // Recarregar lista após assumir
      return resultado;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };
  
  return { chats, loading, error, recarregar: carregarChats, assumirChat };
}
```

### Hook para Mensagens do Chat

```javascript
// hooks/useChatMessages.js
import { useState, useEffect } from 'react';
import { chatsService } from '../services/chats';

export function useChatMessages(chatId) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  
  const carregarMensagens = async (limit = 50, offset = 0) => {
    try {
      setLoading(true);
      const data = await chatsService.mensagensDoChat(chatId, limit, offset);
      setMessages(data.results);
      setTotal(data.total);
    } catch (err) {
      console.error('Erro ao carregar mensagens:', err);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    if (chatId) {
      carregarMensagens();
    }
  }, [chatId]);
  
  const adicionarMensagem = (novaMensagem) => {
    setMessages(prev => [novaMensagem, ...prev]);
    setTotal(prev => prev + 1);
  };
  
  return { messages, loading, total, recarregar: carregarMensagens, adicionarMensagem };
}
```

---

## 🎫 Atendimento

### Serviço de Atendimento

```javascript
// services/atendimento.js
import apiClient from '../api/client';

export const atendimentoService = {
  // Departamentos
  listarDepartamentos: async () => {
    const response = await apiClient.get('/atendimento/departamentos/');
    return response.data;
  },
  
  // Meus atendimentos
  meusAtendimentos: async () => {
    const response = await apiClient.get('/atendimento/atendimentos/meus-atendimentos/');
    return response.data;
  },
  
  // Finalizar
  finalizar: async (id, observacoes) => {
    const response = await apiClient.post(`/atendimento/atendimentos/${id}/finalizar/`, {
      observacoes
    });
    return response.data;
  },
  
  // Transferir
  transferir: async (id, atendenteDestinoId, motivo) => {
    const response = await apiClient.post(`/atendimento/atendimentos/${id}/transferir/`, {
      atendente_destino_id: atendenteDestinoId,
      motivo
    });
    return response.data;
  }
};
```

---

## 🔔 Notificações e Presença

### Gerenciador de Presença

```javascript
// services/presence.js
import apiClient from '../api/client';

export const presenceService = {
  meuStatus: async () => {
    const response = await apiClient.get('/presence/me/');
    return response.data;
  },
  
  alterarStatus: async (status, message = '') => {
    const response = await apiClient.post('/presence/set-status/', {
      status,
      message
    });
    return response.data;
  },
  
  heartbeat: async () => {
    const response = await apiClient.post('/presence/heartbeat/');
    return response.data;
  },
  
  // Iniciar heartbeat automático
  iniciarHeartbeat: () => {
    const interval = setInterval(async () => {
      try {
        await presenceService.heartbeat();
      } catch (error) {
        console.error('Erro no heartbeat:', error);
      }
    }, 30000); // A cada 30 segundos
    
    return () => clearInterval(interval);
  }
};
```

---

## 📊 Tratamento de Erros

```javascript
// utils/errorHandler.js
export function handleApiError(error) {
  if (error.response) {
    // Erro da API
    const status = error.response.status;
    const data = error.response.data;
    
    switch (status) {
      case 400:
        return {
          message: 'Dados inválidos',
          fields: data // erros de validação por campo
        };
      case 401:
        return {
          message: 'Não autenticado. Faça login novamente.',
          redirect: '/login'
        };
      case 403:
        return {
          message: 'Você não tem permissão para esta ação.'
        };
      case 404:
        return {
          message: 'Recurso não encontrado.'
        };
      case 423:
        return {
          message: 'Recurso temporariamente bloqueado.',
          detail: data.detail
        };
      case 500:
        return {
          message: 'Erro no servidor. Tente novamente mais tarde.'
        };
      default:
        return {
          message: data.detail || data.error || 'Erro desconhecido'
        };
    }
  } else if (error.request) {
    // Sem resposta do servidor
    return {
      message: 'Servidor não respondeu. Verifique sua conexão.'
    };
  } else {
    // Erro na configuração da requisição
    return {
      message: error.message || 'Erro ao processar requisição'
    };
  }
}
```

---

## 🔗 Links Úteis

### Documentação API
- [Lista Completa de Endpoints](./API_ENDPOINTS_COMPLETE.md) - 100 endpoints
- [Referência API Detalhada](./API_REFERENCE.md)
- [API de Chats](./CHATS_API.md) - **NOVO** - Conversas e atendimento

### Guias e Tutoriais
- [Guia de Testes com Stub](./WHATSAPP_STUB_TESTING.md)
- [Eventos de Notificação](./NOTIFICATION_EVENTS.md)
- [Issue #83 - Solução](./ISSUE_83_SOLUCAO.md) - Endpoint inject-incoming

### Configuração
- [Variáveis de Ambiente](./ENVIRONMENT_VARIABLES.md)
- [Configuração CORS](./CORS_CONFIGURATION.md)

---

**Versão**: v1  
**Atualizado**: 12/10/2025  
**Issues Resolvidas**: #83, #85

