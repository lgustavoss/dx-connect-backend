# 💬 API de Chats - DX Connect (Issue #85)

## 📋 Índice
- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Endpoints](#endpoints)
- [Fluxo de Atendimento](#fluxo-de-atendimento)
- [Eventos WebSocket](#eventos-websocket)
- [Isolamento de Histórico](#isolamento-de-histórico)
- [Exemplos de Uso](#exemplos-de-uso)

---

## 🎯 Visão Geral

API completa para gerenciamento de conversas/chats de atendimento, com:

✅ **Listagem de Conversas** - Todos os chats com última mensagem e contadores  
✅ **Histórico Isolado** - Mensagens apenas do atendimento atual  
✅ **Auto-criação de Atendimentos** - Nova mensagem = novo atendimento automático  
✅ **Alertas Sonoros** - Notificação quando nova conversa chega  
✅ **Gerenciamento Completo** - Aceitar, transferir e encerrar chats

---

## 🏗️ Arquitetura

### Fluxo de Dados

```
Nova Mensagem WhatsApp
         ↓
  ChatService.processar_nova_mensagem_recebida()
         ↓
    Já existe atendimento ativo?
         ├─ SIM → Atualiza contador
         │         └→ Emite evento 'new_message'
         │
         └─ NÃO → Cria Cliente (se não existir)
                   └→ Cria Atendimento (status: aguardando)
                   └→ Adiciona à FilaAtendimento
                   └→ Emite evento 'new_chat' + ALERTA SONORO 🔔
```

### Modelos Envolvidos

| Modelo | Responsabilidade |
|--------|------------------|
| `WhatsAppMessage` | Armazena todas as mensagens |
| `Atendimento` | Representa um ciclo de conversa (início → fim) |
| `FilaAtendimento` | Fila de espera para atribuição |
| `Cliente` | Dados do cliente |
| `Departamento` | Organização da equipe |

---

## 🔌 Endpoints

Base URL: `/api/v1/chats/`

### 1. Listar Chats

```http
GET /api/v1/chats/
Authorization: Bearer {token}

Query Params:
- status: aguardando, em_atendimento, pausado, finalizado
- atendente: ID do atendente
- departamento: ID do departamento
- sort: lastMessage, priority, created, updated
- order: asc, desc
- page: número da página
- size: itens por página
```

**Resposta:**
```json
[
  {
    "chat_id": "5511999999999",
    "numero_whatsapp": "5511999999999",
    "cliente_id": 1,
    "cliente_nome": "João Silva Ltda",
    "cliente_email": "contato@joao.com",
    "atendimento_id": 42,
    "status": "em_atendimento",
    "prioridade": "normal",
    "atendente_id": 5,
    "atendente_nome": "Maria Santos",
    "departamento_id": 1,
    "departamento_nome": "Suporte",
    "ultima_mensagem_texto": "Preciso de ajuda urgente!",
    "ultima_mensagem_em": "2025-10-12T15:30:00Z",
    "ultima_mensagem_tipo": "text",
    "ultima_mensagem_direcao": "inbound",
    "total_mensagens": 15,
    "mensagens_nao_lidas": 3,
    "criado_em": "2025-10-12T14:00:00Z",
    "atualizado_em": "2025-10-12T15:30:00Z"
  }
]
```

**Comportamento Padrão:**
- Não mostra chats finalizados (use `?status=finalizado` para ver)
- Atendentes veem apenas seus chats + chats aguardando
- Admins veem todos os chats
- Ordenação padrão: última mensagem (mais recente primeiro)

---

### 2. Detalhar Chat

```http
GET /api/v1/chats/{chat_id}/
Authorization: Bearer {token}
```

**Resposta:**
```json
{
  "id": 42,
  "chat_id": "5511999999999",
  "numero_whatsapp": "5511999999999",
  "status": "em_atendimento",
  "prioridade": "normal",
  "cliente": 1,
  "cliente_nome": "João Silva Ltda",
  "cliente_email": "contato@joao.com",
  "cliente_telefone": "5511999999999",
  "atendente": 5,
  "atendente_nome": "Maria Santos",
  "atendente_username": "maria",
  "departamento": 1,
  "departamento_nome": "Suporte",
  "departamento_cor": "#3B82F6",
  "duracao_minutos": 45,
  "tempo_primeira_resposta_minutos": 2,
  "total_mensagens_cliente": 10,
  "total_mensagens_atendente": 12,
  "total_mensagens": 22,
  "mensagens_nao_lidas": 3,
  "avaliacao": null,
  "comentario_avaliacao": "",
  "observacoes": "",
  "criado_em": "2025-10-12T14:00:00Z",
  "iniciado_em": "2025-10-12T14:05:00Z",
  "primeira_resposta_em": "2025-10-12T14:07:00Z",
  "finalizado_em": null,
  "atualizado_em": "2025-10-12T15:30:00Z"
}
```

---

### 3. Mensagens do Chat

```http
GET /api/v1/chats/{chat_id}/messages/
Authorization: Bearer {token}

Query Params:
- limit: número de mensagens (padrão: 50)
- offset: paginação
```

**Resposta:**
```json
{
  "total": 22,
  "limit": 50,
  "offset": 0,
  "results": [
    {
      "id": 150,
      "message_id": "msg_abc123",
      "direction": "inbound",
      "message_type": "text",
      "chat_id": "5511999999999",
      "contact_number": "5511999999999",
      "contact_name": "João Silva",
      "text_content": "Preciso de ajuda urgente!",
      "media_url": null,
      "media_mime_type": null,
      "status": "delivered",
      "is_from_me": false,
      "from_name": "João Silva",
      "is_from_agent": false,
      "latency_ms": 234,
      "is_latency_ok": true,
      "created_at": "2025-10-12T15:30:00Z",
      "sent_at": null,
      "delivered_at": "2025-10-12T15:30:00Z",
      "read_at": null
    }
  ]
}
```

**⚠️ IMPORTANTE:** Este endpoint retorna **APENAS mensagens do atendimento atual**, não mostra histórico de atendimentos anteriores!

---

### 4. Aceitar Chat

```http
POST /api/v1/chats/{chat_id}/aceitar/
Authorization: Bearer {token}

Body (opcional):
{
  "atendente_id": 5,  // Opcional: usa usuário atual se não fornecido
  "observacoes": "Cliente solicitou urgência"
}
```

**Resposta:**
```json
{
  "id": 42,
  "chat_id": "5511999999999",
  "status": "em_atendimento",
  "atendente": 5,
  "atendente_nome": "Maria Santos",
  "iniciado_em": "2025-10-12T15:35:00Z",
  ...
}
```

**Comportamento:**
1. Valida que chat está em `aguardando`
2. Atribui atendente (usuário atual ou especificado)
3. Muda status para `em_atendimento`
4. Remove da `FilaAtendimento`
5. Emite evento WebSocket `chat_accepted`

**Permissões:**
- Atendente pode aceitar para si mesmo
- Apenas admin pode aceitar para outro atendente

---

### 5. Transferir Chat

```http
POST /api/v1/chats/{chat_id}/transferir/
Authorization: Bearer {token}

Body:
{
  "atendente_destino_id": 8,  // Obrigatório
  "departamento_destino_id": 2,  // Opcional
  "motivo": "Cliente solicitou especialista"  // Obrigatório
}
```

**Resposta:**
```json
{
  "message": "Chat transferido com sucesso",
  "transferencia_id": 1,
  "atendente_destino": {
    "id": 8,
    "nome": "Pedro Oliveira"
  }
}
```

**Comportamento:**
1. Valida permissão (só atendente responsável ou admin)
2. Cria registro em `TransferenciaAtendimento` (auditoria)
3. Atualiza `atendente` e opcionalmente `departamento`
4. Emite evento WebSocket `chat_transferred`

---

### 6. Encerrar Chat

```http
POST /api/v1/chats/{chat_id}/encerrar/
Authorization: Bearer {token}

Body (opcional):
{
  "observacoes": "Problema resolvido, cliente satisfeito",
  "solicitar_avaliacao": true  // Padrão: true
}
```

**Resposta:**
```json
{
  "message": "Chat encerrado com sucesso",
  "atendimento_id": 42,
  "finalizado_em": "2025-10-12T16:00:00Z"
}
```

**Comportamento:**
1. Valida permissão (só atendente responsável ou admin)
2. Muda status para `finalizado`
3. Registra `finalizado_em` e `observacoes`
4. Emite evento WebSocket `chat_closed`
5. (Futuro) Envia solicitação de avaliação se `solicitar_avaliacao=true`

---

## 🔄 Fluxo de Atendimento

### Cenário 1: Nova Conversa

```
1. Cliente envia primeira mensagem via WhatsApp
   ↓
2. Webhook/Inject recebe → cria WhatsAppMessage
   ↓
3. ChatService detecta: "novo chat_id"
   ↓
4. Cria Cliente (se não existir)
   ↓
5. Cria Atendimento (status: aguardando)
   ↓
6. Adiciona à FilaAtendimento
   ↓
7. Emite evento WebSocket 'new_chat' 🔔
   ↓
8. Frontend toca alerta sonoro
   ↓
9. Atendente clica "Aceitar"
   ↓
10. POST /chats/{chat_id}/aceitar/
   ↓
11. Status → em_atendimento
   ↓
12. Atendente vinculado ao chat
```

### Cenário 2: Mensagem em Chat Existente

```
1. Cliente envia nova mensagem no chat em andamento
   ↓
2. WhatsAppMessage criada
   ↓
3. ChatService detecta: "atendimento ativo existe"
   ↓
4. Atualiza contador: total_mensagens_cliente++
   ↓
5. Emite evento 'new_message' (sem alerta sonoro)
   ↓
6. Frontend atualiza badge de não lidas
```

---

## 🔌 Eventos WebSocket

### Evento: new_chat (Nova Conversa)

```json
{
  "event": "new_chat",
  "play_sound": true,  // ← ALERTA SONORO!
  "data": {
    "chat_id": "5511999999999",
    "atendimento_id": 42,
    "numero_whatsapp": "5511999999999",
    "cliente_id": 1,
    "cliente_nome": "João Silva Ltda",
    "departamento_id": 1,
    "departamento_nome": "Suporte",
    "mensagem_inicial": "Olá, preciso de ajuda urgente!",
    "criado_em": "2025-10-12T15:00:00Z",
    "prioridade": "normal"
  }
}
```

**Frontend deve:**
1. ✅ Tocar som de alerta
2. ✅ Mostrar notificação desktop
3. ✅ Adicionar chat na lista
4. ✅ Atualizar badge de chats aguardando

---

### Evento: new_message (Mensagem em Chat Existente)

```json
{
  "event": "new_message",
  "play_sound": false,  // Sem alerta
  "data": {
    "chat_id": "5511999999999",
    "atendimento_id": 42,
    "message_id": "msg_xyz789",
    "texto": "Mais uma pergunta...",
    "tipo": "text",
    "de": "João Silva",
    "criado_em": "2025-10-12T15:30:00Z"
  }
}
```

**Frontend deve:**
1. ✅ Incrementar badge de não lidas
2. ✅ Atualizar última mensagem na lista
3. ✅ Se chat aberto, adicionar mensagem ao histórico

---

### Evento: chat_accepted (Chat Aceito)

```json
{
  "event": "chat_accepted",
  "data": {
    "chat_id": "5511999999999",
    "atendimento_id": 42,
    "atendente_id": 5,
    "atendente_nome": "Maria Santos",
    "status": "em_atendimento"
  }
}
```

---

### Evento: chat_transferred (Chat Transferido)

```json
{
  "event": "chat_transferred",
  "data": {
    "chat_id": "5511999999999",
    "atendimento_id": 42,
    "atendente_origem_id": 5,
    "atendente_destino_id": 8,
    "atendente_destino_nome": "Pedro Oliveira",
    "motivo": "Cliente solicitou especialista"
  }
}
```

---

### Evento: chat_closed (Chat Encerrado)

```json
{
  "event": "chat_closed",
  "data": {
    "chat_id": "5511999999999",
    "atendimento_id": 42,
    "atendente_id": 5,
    "finalizado_em": "2025-10-12T16:00:00Z"
  }
}
```

---

## 🔒 Isolamento de Histórico

### Garantia de Privacidade

**Cada `Atendimento` tem seu próprio histórico isolado:**

```sql
SELECT * FROM whatsapp_whatsappmessage
WHERE chat_id = '5511999999999'
  AND created_at >= atendimento.criado_em  -- ← ISOLAMENTO!
```

### Exemplo Prático:

**Atendimento #1** (encerrado em 10/10/2025 às 14h)
- Mensagens: 20 mensagens trocadas
- Status: finalizado

**Atendimento #2** (iniciado em 12/10/2025 às 10h)
- Mensagens: **APENAS as novas** a partir de 12/10 10h
- Não mostra as 20 mensagens do Atendimento #1 ✅

### Benefícios:

- ✅ **Privacidade**: Atendente novo não vê histórico anterior
- ✅ **Performance**: Queries mais rápidas
- ✅ **LGPD**: Permite excluir históricos antigos
- ✅ **Clareza**: Cada atendimento é uma "sessão" isolada

---

## 💻 Exemplos de Uso

### Frontend: Listar Chats

```javascript
// services/chats.js
import apiClient from '../api/client';

export const chatsService = {
  listarChats: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.atendente) params.append('atendente', filters.atendente);
    if (filters.sort) params.append('sort', filters.sort);
    if (filters.order) params.append('order', filters.order);
    
    const response = await apiClient.get(`/chats/?${params}`);
    return response.data;
  },
  
  detalharChat: async (chatId) => {
    const response = await apiClient.get(`/chats/${chatId}/`);
    return response.data;
  },
  
  mensagensDoChat: async (chatId, limit = 50, offset = 0) => {
    const response = await apiClient.get(
      `/chats/${chatId}/messages/?limit=${limit}&offset=${offset}`
    );
    return response.data;
  },
  
  aceitarChat: async (chatId) => {
    const response = await apiClient.post(`/chats/${chatId}/aceitar/`, {});
    return response.data;
  },
  
  encerrarChat: async (chatId, observacoes = '') => {
    const response = await apiClient.post(`/chats/${chatId}/encerrar/`, {
      observacoes,
      solicitar_avaliacao: true
    });
    return response.data;
  }
};
```

### Hook React

```javascript
// hooks/useChats.js
import { useState, useEffect } from 'react';
import { chatsService } from '../services/chats';

export function useChats(filters = {}) {
  const [chats, setChats] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const carregarChats = async () => {
    try {
      setLoading(true);
      const data = await chatsService.listarChats(filters);
      setChats(data);
    } catch (error) {
      console.error('Erro ao carregar chats:', error);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    carregarChats();
  }, [JSON.stringify(filters)]);
  
  return { chats, loading, recarregar: carregarChats };
}
```

### Componente Lista de Chats

```javascript
// components/ChatsList.jsx
import { useChats } from '../hooks/useChats';
import { useState } from 'react';

function ChatsList() {
  const [filter, setFilter] = useState('all'); // all, aguardando, meus
  const { chats, loading, recarregar } = useChats({
    status: filter === 'aguardando' ? 'aguardando' : undefined,
    atendente: filter === 'meus' ? currentUserId : undefined,
    sort: 'lastMessage',
    order: 'desc'
  });
  
  const handleAceitarChat = async (chatId) => {
    try {
      await chatsService.aceitarChat(chatId);
      recarregar(); // Atualizar lista
      // Abrir chat
      window.location.href = `/chat/${chatId}`;
    } catch (error) {
      alert('Erro ao aceitar chat: ' + error.message);
    }
  };
  
  if (loading) return <div>Carregando...</div>;
  
  return (
    <div className="chats-list">
      {/* Filtros */}
      <div className="filters">
        <button
          className={filter === 'all' ? 'active' : ''}
          onClick={() => setFilter('all')}
        >
          Todos ({chats.length})
        </button>
        <button
          className={filter === 'aguardando' ? 'active' : ''}
          onClick={() => setFilter('aguardando')}
        >
          Aguardando ({chats.filter(c => c.status === 'aguardando').length})
        </button>
        <button
          className={filter === 'meus' ? 'active' : ''}
          onClick={() => setFilter('meus')}
        >
          Meus Atendimentos
        </button>
      </div>
      
      {/* Lista */}
      <div className="chats">
        {chats.map((chat) => (
          <div key={chat.chat_id} className={`chat-item chat-${chat.status}`}>
            <div className="chat-header">
              <h3>{chat.cliente_nome}</h3>
              {chat.mensagens_nao_lidas > 0 && (
                <span className="badge">{chat.mensagens_nao_lidas}</span>
              )}
            </div>
            
            <div className="chat-preview">
              <span className={`direction-${chat.ultima_mensagem_direcao}`}>
                {chat.ultima_mensagem_direcao === 'inbound' ? '📩' : '📤'}
              </span>
              {chat.ultima_mensagem_texto}
            </div>
            
            <div className="chat-meta">
              <span className="time">
                {new Date(chat.ultima_mensagem_em).toLocaleTimeString()}
              </span>
              <span className={`status status-${chat.status}`}>
                {chat.status}
              </span>
            </div>
            
            {chat.status === 'aguardando' && (
              <button
                className="btn-accept"
                onClick={() => handleAceitarChat(chat.chat_id)}
              >
                Aceitar Atendimento
              </button>
            )}
            
            {chat.atendente_nome && (
              <div className="attendant">
                👤 {chat.atendente_nome}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
```

### WebSocket: Ouvir Novos Chats

```javascript
// Em seu hook useWebSocket ou componente principal
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.event === 'new_chat') {
    console.log('🔔 NOVO CHAT!', data.data);
    
    // 1. Tocar alerta sonoro
    if (data.play_sound) {
      const audio = new Audio('/sounds/new-chat.mp3');
      audio.play();
    }
    
    // 2. Mostrar notificação
    if (Notification.permission === 'granted') {
      new Notification('Novo Chat!', {
        body: data.data.mensagem_inicial,
        icon: '/icon.png'
      });
    }
    
    // 3. Atualizar lista de chats
    recarregarChats();
    
    // 4. Atualizar badge
    setBadgeCount(prev => prev + 1);
  }
};
```

---

## 🧪 Testes

### Executar Testes

```bash
docker-compose exec web python manage.py test chats --keepdb
```

### Cobertura

✅ **8 testes implementados**:
1. Listar chats vazia
2. Listar chats com dados
3. Detalhar chat
4. Mensagens do chat
5. Aceitar chat
6. Encerrar chat
7. Processar nova mensagem cria atendimento
8. Mensagem em chat existente não duplica

**Resultado**: ✅ **8/8 testes passando**

---

## 📊 Comparação: Antes vs Depois

### Antes (Issue #85 Aberta)

| Recurso | Status |
|---------|--------|
| Listar conversas | ❌ 404 Not Found |
| Agrupar por chat | ❌ Não existia |
| Aceitar atendimento | ⚠️ Via `/atendimento/` |
| Auto-criar na 1ª msg | ❌ Não existia |
| Alerta novo chat | ❌ Não existia |
| Histórico isolado | ⚠️ Mostrava tudo |

### Depois (Issue #85 Resolvida)

| Recurso | Status |
|---------|--------|
| Listar conversas | ✅ `/api/v1/chats/` |
| Agrupar por chat | ✅ Automático |
| Aceitar atendimento | ✅ `/chats/{id}/aceitar/` |
| Auto-criar na 1ª msg | ✅ Automático |
| Alerta novo chat | ✅ WebSocket + Som |
| Histórico isolado | ✅ Por atendimento |

---

## 🔗 Integração com Outros Endpoints

### Relação com WhatsApp

```http
# Injetar mensagem de teste (cria chat automaticamente!)
POST /api/v1/whatsapp/inject-incoming/
{
  "from": "5511999999999",
  "payload": {
    "type": "text",
    "text": "Olá, preciso de ajuda!"
  }
}

# Verificar que chat foi criado
GET /api/v1/chats/
→ Retorna novo chat em "aguardando"
```

### Relação com Atendimento

```http
# Buscar atendimentos (visão de gestão)
GET /api/v1/atendimento/atendimentos/

# Buscar chats (visão de atendente)
GET /api/v1/chats/
```

**Diferença:**
- `/atendimento/` = Visão administrativa, métricas, relatórios
- `/chats/` = Visão operacional, interface de chat

---

## 📚 Referências

- **Issue**: #85 - Implementar API de Chats e Processamento de Mensagens WebSocket
- **Sprint**: 3.5 (Complemento da Sprint 3)
- **Arquivos**:
  - `chats/serializers.py` - Serializers de Chat
  - `chats/views.py` - ViewSet e actions
  - `chats/service.py` - Lógica de negócio
  - `chats/tests.py` - Testes unitários
- **Relacionado**:
  - [WhatsApp - Sessões e Eventos](./WHATSAPP_SESSION_EVENTS.md)
  - [API Reference](./API_REFERENCE.md)
  - [Guia de Testes com Stub](./WHATSAPP_STUB_TESTING.md)

---

## 🚀 Próximos Passos (Melhorias Futuras)

1. ⏳ Implementar envio de solicitação de avaliação
2. ⏳ Adicionar filtro por período
3. ⏳ Adicionar busca textual em mensagens
4. ⏳ Implementar paginação no /chats/
5. ⏳ Adicionar métricas agregadas (/chats/stats/)
6. ⏳ Implementar tags/categorias de atendimento

---

**Atualizado em**: 12 de Outubro de 2025  
**Versão da API**: v1  
**Status**: ✅ Implementado e Testado

