# 🐛 Issue #83 - Solução: Endpoint de Injeção de Mensagens

## 📋 Problema Relatado

O frontend estava encontrando erro `404 Not Found` ao tentar usar o endpoint `/api/v1/whatsapp/inject-incoming/` para injetar mensagens de teste, conforme documentado no guia de testes.

### Erro nos Logs:
```
POST /api/v1/whatsapp/inject-incoming/ 404
```

### Causa Raiz:
O endpoint HTTP para injeção de mensagens estava **documentado mas não implementado**. A funcionalidade existia apenas via **WebSocket**.

---

## ✅ Solução Implementada

### 1. Novo Endpoint HTTP

Criado endpoint REST para injetar mensagens de teste:

**URL**: `POST /api/v1/whatsapp/inject-incoming/`  
**Autenticação**: JWT Bearer Token  
**Permissão**: IsAuthenticated

### 2. Arquivos Modificados

#### `whatsapp/views.py`
- ✅ Adicionada classe `WhatsAppInjectIncomingView`
- ✅ Validação de dados de entrada
- ✅ Suporte para todos os tipos de mensagem (text, image, audio, video, document)
- ✅ Tratamento de erros específicos
- ✅ Logs informativos
- ✅ Documentação OpenAPI/Swagger

#### `whatsapp/urls.py`
- ✅ Registrada rota `inject-incoming/`
- ✅ Importado `WhatsAppInjectIncomingView`

#### `whatsapp/tests/test_inject_incoming.py`
- ✅ Criado arquivo de testes completo
- ✅ 11 testes cobrindo todos os cenários
- ✅ 100% de cobertura de código da nova view

---

## 📚 Uso do Endpoint

### Request

```http
POST /api/v1/whatsapp/inject-incoming/
Authorization: Bearer {seu_token_jwt}
Content-Type: application/json

{
  "from": "5511999999999",
  "chat_id": "5511999999999",
  "payload": {
    "type": "text",
    "text": "Olá, preciso de ajuda!",
    "contact_name": "João Silva"
  }
}
```

### Response (Sucesso - 200)

```json
{
  "message": "Mensagem de teste injetada com sucesso",
  "message_id": "msg_abc123",
  "database_id": 42,
  "data": {
    "id": 42,
    "message_id": "msg_abc123",
    "direction": "inbound",
    "message_type": "text",
    "contact_number": "5511999999999",
    "contact_name": "João Silva",
    "text_content": "Olá, preciso de ajuda!",
    "status": "delivered",
    "created_at": "2025-10-12T10:00:00Z",
    "delivered_at": "2025-10-12T10:00:00Z"
  }
}
```

### Erros Possíveis

| Status | Erro | Causa |
|--------|------|-------|
| `400` | Campo "from" é obrigatório | Faltou o campo `from` no body |
| `400` | Campo "payload" é obrigatório | Faltou o campo `payload` no body |
| `400` | Tipo de mensagem inválido | `payload.type` não é válido |
| `400` | Campo "payload.text" é obrigatório | Mensagem de texto sem conteúdo |
| `401` | Unauthorized | Token JWT inválido ou ausente |
| `404` | Sessão WhatsApp não encontrada | Usuário não tem sessão ativa |
| `500` | Erro ao injetar mensagem | Erro interno no processamento |

---

## 🧪 Testes

### Executar Testes

```bash
docker-compose exec web python manage.py test whatsapp.tests.test_inject_incoming --keepdb
```

### Cobertura de Testes

✅ **11 testes implementados**:

1. ✅ Injetar mensagem de texto com sucesso
2. ✅ Erro quando 'from' não é fornecido
3. ✅ Erro quando 'payload' não é fornecido
4. ✅ Erro com tipo de mensagem inválido
5. ✅ Erro quando mensagem de texto não tem conteúdo
6. ✅ Injeção com chat_id customizado
7. ✅ Erro quando usuário não tem sessão
8. ✅ Endpoint requer autenticação
9. ✅ Injetar mensagem com imagem
10. ✅ Múltiplas mensagens do mesmo contato
11. ✅ Mensagem criada com status delivered

**Resultado**: ✅ **Todos os testes passando**

---

## 💻 Exemplos de Uso Frontend

### JavaScript/Fetch

```javascript
async function injectTestMessage(token, from, text, contactName = '') {
  try {
    const response = await fetch('http://localhost:8001/api/v1/whatsapp/inject-incoming/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        from: from,
        payload: {
          type: 'text',
          text: text,
          contact_name: contactName || from
        }
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Erro ao injetar mensagem');
    }
    
    const data = await response.json();
    console.log('✅ Mensagem injetada:', data);
    return data;
  } catch (error) {
    console.error('❌ Erro:', error.message);
    throw error;
  }
}

// Uso
injectTestMessage(myToken, '5511999999999', 'Olá, preciso de ajuda!', 'João Silva');
```

### Axios

```javascript
import axios from 'axios';

const injectMessage = async (from, text, contactName) => {
  try {
    const response = await axios.post(
      'http://localhost:8001/api/v1/whatsapp/inject-incoming/',
      {
        from,
        payload: {
          type: 'text',
          text,
          contact_name: contactName
        }
      },
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      }
    );
    
    return response.data;
  } catch (error) {
    console.error('Erro:', error.response?.data?.error || error.message);
    throw error;
  }
};
```

### Postman

**URL**: `POST http://localhost:8001/api/v1/whatsapp/inject-incoming/`

**Headers**:
```
Authorization: Bearer seu_token_aqui
Content-Type: application/json
```

**Body** (raw JSON):
```json
{
  "from": "5511999999999",
  "payload": {
    "type": "text",
    "text": "Teste via Postman",
    "contact_name": "Postman User"
  }
}
```

---

## 🎯 Comparação: HTTP vs WebSocket

### Via HTTP (Novo - Recomendado)

**Vantagens:**
- ✅ Não precisa de conexão WebSocket
- ✅ Mais fácil para testes automatizados
- ✅ Funciona com Postman/Insomnia
- ✅ Retorna confirmação imediata
- ✅ Ideal para CI/CD

**Desvantagens:**
- ❌ Não é tempo real (precisa polling ou WS separado)

### Via WebSocket (Já Existia)

**Vantagens:**
- ✅ Tempo real
- ✅ Recebe confirmação via WS
- ✅ Bidirecional

**Desvantagens:**
- ❌ Precisa manter conexão aberta
- ❌ Mais complexo para testes automatizados

---

## 📊 Impacto

### Antes
- ❌ Frontend recebia 404
- ❌ Testes automatizados não funcionavam
- ❌ Postman não funcionava
- ⚠️ Dependia de WebSocket para tudo

### Depois
- ✅ Frontend funciona normalmente
- ✅ Testes automatizados OK
- ✅ Postman/Insomnia OK
- ✅ 2 opções: HTTP ou WebSocket

---

## 🚀 Próximos Passos

1. ✅ **Frontend pode continuar desenvolvimento**
2. ✅ **Testes de integração podem ser implementados**
3. ✅ **CI/CD pode incluir testes de injeção**
4. ⏳ **Considerar adicionar rate limiting** (futuro)
5. ⏳ **Considerar desabilitar em produção** (futuro, via env var)

---

## 📝 Checklist de Validação

- [x] Endpoint implementado
- [x] Testes unitários passando (11/11)
- [x] Documentação atualizada
- [x] Swagger/OpenAPI atualizado
- [x] Logs informativos adicionados
- [x] Validações de entrada implementadas
- [x] Tratamento de erros completo
- [x] Permissões configuradas (IsAuthenticated)
- [x] Guias de uso atualizados

---

## 🔗 Referências

- **Issue**: #83
- **PR**: (a ser criado)
- **Documentação**: 
  - [API Reference](./API_REFERENCE.md) - Seção WhatsApp
  - [Guia de Testes com Stub](./WHATSAPP_STUB_TESTING.md) - Seção 5
  - [Frontend API Guide](./FRONTEND_API_GUIDE.md)
- **Arquivos Modificados**:
  - `whatsapp/views.py` (+122 linhas)
  - `whatsapp/urls.py` (+2 linhas)
  - `whatsapp/tests/test_inject_incoming.py` (+265 linhas - novo)
  - `docs/API_REFERENCE.md` (atualizado)
  - `docs/WHATSAPP_STUB_TESTING.md` (atualizado)

---

**Data da Solução**: 12 de Outubro de 2025  
**Status**: ✅ Resolvido e Testado  
**Impacto**: Frontend pode voltar ao desenvolvimento

