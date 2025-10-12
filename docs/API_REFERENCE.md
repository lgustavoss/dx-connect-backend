# 📘 API Reference - DX Connect Backend

## 🎯 Visão Geral

Backend API para sistema de gestão e atendimento ao cliente DX Connect.

**Base URL**: `http://localhost:8001/api/v1/`

**Autenticação**: JWT Bearer Token

**Formato**: JSON

**Versão**: v1

---

## 📑 Índice

1. [Autenticação](#autenticação)
2. [Clientes](#clientes)
3. [Contatos](#contatos)
4. [Documentos](#documentos)
5. [WhatsApp](#whatsapp)
6. [Atendimento](#atendimento)
7. [Configurações](#configurações)
8. [Integrações](#integrações)
9. [WebSocket](#websocket)

---

## 🔐 Autenticação

### Obter Token JWT
```http
POST /api/v1/auth/token/
Content-Type: application/json

{
  "username": "admin",
  "password": "senha123"
}
```

**Resposta:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Refresh Token
```http
POST /api/v1/auth/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Usar Token
```http
GET /api/v1/clientes/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Meus Dados
```http
GET /api/v1/me/
Authorization: Bearer {token}
```

**Resposta:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "display_name": "Administrador"
}
```

---

## 👥 Clientes

### Listar Clientes
```http
GET /api/v1/clientes/
Authorization: Bearer {token}

Query Params:
- status: ativo, inativo, suspenso
- tipo_pessoa: fisica, juridica
- search: busca por nome, CNPJ/CPF, email
- ordering: razao_social, created_at, -updated_at
```

### Criar Cliente
```http
POST /api/v1/clientes/
Authorization: Bearer {token}
Content-Type: application/json

{
  "razao_social": "Empresa XYZ Ltda",
  "nome_fantasia": "XYZ",
  "tipo_pessoa": "juridica",
  "cnpj_cpf": "12345678000190",
  "email": "contato@xyz.com.br",
  "telefone": "11999999999",
  "endereco": "Rua das Flores, 123",
  "numero": "123",
  "bairro": "Centro",
  "cidade": "São Paulo",
  "estado": "SP",
  "cep": "01234-567"
}
```

### Buscar por CEP
```http
GET /api/v1/integrations/cep/01001-000/
```

**Resposta:**
```json
{
  "cep": "01001-000",
  "logradouro": "Praça da Sé",
  "complemento": "lado ímpar",
  "bairro": "Sé",
  "cidade": "São Paulo",
  "estado": "SP"
}
```

---

## 📞 Contatos

### Listar Contatos
```http
GET /api/v1/contatos/?cliente={cliente_id}
Authorization: Bearer {token}
```

### Criar Contato
```http
POST /api/v1/contatos/
Authorization: Bearer {token}

{
  "cliente": 1,
  "nome": "João Silva",
  "cargo": "Gerente",
  "email": "joao@xyz.com.br",
  "telefone": "11988887777",
  "whatsapp": "11988887777",
  "is_principal": true
}
```

---

## 📄 Documentos

### Listar Documentos
```http
GET /api/v1/documentos/?cliente={cliente_id}
Authorization: Bearer {token}

Query Params:
- tipo_documento: contrato, boleto, proposta, certificado
- status: gerado, enviado, assinado, cancelado
- origem: manual, gerado, importado
```

### Upload de Documento
```http
POST /api/v1/documentos/
Authorization: Bearer {token}
Content-Type: multipart/form-data

{
  "cliente": 1,
  "nome": "Contrato de Serviços 2025",
  "tipo_documento": "contrato",
  "arquivo": <file>,
  "descricao": "Contrato anual de manutenção"
}
```

### Gerar Contrato Automático
```http
POST /api/v1/documentos/gerar-contrato/
Authorization: Bearer {token}

{
  "cliente_id": 1,
  "template_nome": "contrato_padrao",
  "dados_contrato": {
    "valor_servico": "5000.00",
    "data_inicio": "2025-01-01",
    "data_fim": "2025-12-31",
    "prazo_contrato": "12 meses"
  }
}
```

### Gerar Boleto
```http
POST /api/v1/documentos/gerar-boleto/
Authorization: Bearer {token}

{
  "cliente_id": 1,
  "dados_boleto": {
    "valor_total": "1500.00",
    "data_vencimento": "2025-11-30",
    "descricao_servicos": "Mensalidade Novembro 2025"
  }
}
```

---

## 💬 WhatsApp

### Base URL
`/api/v1/whatsapp/`

### Sessões

#### Iniciar Sessão
```http
POST /api/v1/whatsapp/sessions/start/
Authorization: Bearer {token}
```

**Resposta:**
```json
{
  "session_id": 1,
  "status": "connecting",
  "message": "Sessão iniciada com sucesso"
}
```

#### Status da Sessão
```http
GET /api/v1/whatsapp/sessions/status/
Authorization: Bearer {token}
```

**Resposta:**
```json
{
  "session_id": 1,
  "status": "ready",
  "is_connected": true,
  "phone_number": "5511999999999",
  "uptime_seconds": 3600,
  "total_messages_sent": 150,
  "total_messages_received": 230
}
```

#### Parar Sessão
```http
POST /api/v1/whatsapp/sessions/stop/
Authorization: Bearer {token}
```

#### Métricas da Sessão
```http
GET /api/v1/whatsapp/sessions/{id}/metrics/
Authorization: Bearer {token}
```

#### Exportar Sessão (Backup)
```http
GET /api/v1/whatsapp/sessions/{id}/export/
Authorization: Bearer {token}
```

Retorna arquivo JSON para download.

#### Importar Sessão (Restore)
```http
POST /api/v1/whatsapp/sessions/import/
Authorization: Bearer {token}

{
  "device_name": "DX Connect Web",
  "session_data": "encrypted_data...",
  "auto_reconnect": true
}
```

#### Forçar Reconexão
```http
POST /api/v1/whatsapp/sessions/{id}/reconnect/
Authorization: Bearer {token}
```

---

### Mensagens

#### Enviar Mensagem
```http
POST /api/v1/whatsapp/send/
Authorization: Bearer {token}

{
  "to": "5511999999999",
  "type": "text",
  "text": "Olá! Como posso ajudar?",
  "client_message_id": "custom-id-123"
}
```

**Resposta:**
```json
{
  "message": "Mensagem enfileirada para envio",
  "task_id": "a1b2c3d4-...",
  "to": "5511999999999",
  "status": "queued"
}
```

#### Enviar Imagem
```http
POST /api/v1/whatsapp/send/

{
  "to": "5511999999999",
  "type": "image",
  "media_url": "https://example.com/image.jpg",
  "text": "Legenda da imagem"
}
```

#### Listar Mensagens
```http
GET /api/v1/whatsapp/messages/
Authorization: Bearer {token}

Query Params:
- direction: inbound, outbound
- message_type: text, image, audio, video, document
- status: queued, sent, delivered, read
- chat_id: filtrar por chat
```

#### Estatísticas de Latência
```http
GET /api/v1/whatsapp/messages/latency-stats/
Authorization: Bearer {token}
```

**Resposta:**
```json
{
  "total_messages": 380,
  "avg_latency_to_sent_ms": 1250.5,
  "messages_over_5s": 3,
  "latency_acceptable_rate": 98.0
}
```

#### Webhook (Receber Mensagens Externas)
```http
POST /api/v1/whatsapp/webhook/
Content-Type: application/json

{
  "event": "message_received",
  "data": {
    "from": "5511999999999",
    "message": "Texto da mensagem",
    "message_id": "abc123",
    "timestamp": "2025-10-11T10:00:00Z"
  },
  "version": "v1"
}
```

---

## 🎫 Atendimento

### Base URL
`/api/v1/atendimento/`

### Departamentos

#### Listar Departamentos
```http
GET /api/v1/atendimento/departamentos/
Authorization: Bearer {token}
```

**Resposta:**
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "nome": "Vendas",
      "descricao": "Atendimento comercial",
      "cor": "#10B981",
      "total_atendentes": 5,
      "total_em_fila": 3,
      "total_em_atendimento": 8,
      "max_atendimentos_simultaneos": 3,
      "tempo_resposta_esperado_minutos": 15,
      "ativo": true
    }
  ]
}
```

#### Criar Departamento
```http
POST /api/v1/atendimento/departamentos/

{
  "nome": "Suporte",
  "descricao": "Suporte técnico",
  "cor": "#3B82F6",
  "max_atendimentos_simultaneos": 5,
  "tempo_resposta_esperado_minutos": 10
}
```

---

### Filas

#### Adicionar Cliente na Fila
```http
POST /api/v1/atendimento/filas/

{
  "departamento": 1,
  "cliente": 5,
  "chat_id": "5511999999999",
  "numero_whatsapp": "5511999999999",
  "mensagem_inicial": "Preciso de ajuda com...",
  "prioridade": "alta"
}
```

**Prioridades**: `baixa`, `normal`, `alta`, `urgente`

#### Distribuir Automaticamente
```http
POST /api/v1/atendimento/filas/distribuir/

{
  "departamento_id": 1
}
```

**Resposta:**
```json
{
  "message": "3 atendimentos distribuídos",
  "distribuidos": 3
}
```

---

### Atendimentos

#### Meus Atendimentos Ativos
```http
GET /api/v1/atendimento/atendimentos/meus-atendimentos/
Authorization: Bearer {token}
```

**Resposta:**
```json
[
  {
    "id": 123,
    "cliente_nome": "Empresa XYZ",
    "status": "em_atendimento",
    "prioridade": "alta",
    "chat_id": "5511999999999",
    "duracao_minutos": 15,
    "total_mensagens_cliente": 8,
    "total_mensagens_atendente": 10
  }
]
```

#### Finalizar Atendimento
```http
POST /api/v1/atendimento/atendimentos/{id}/finalizar/

{
  "observacoes": "Cliente satisfeito, problema resolvido"
}
```

#### Transferir Atendimento
```http
POST /api/v1/atendimento/atendimentos/{id}/transferir/

{
  "atendente_destino_id": 5,
  "motivo": "Cliente solicitou especialista",
  "departamento_destino_id": 2
}
```

**Resposta:**
```json
{
  "message": "Atendimento transferido com sucesso",
  "transferencia": {
    "id": 1,
    "atendente_origem_nome": "João",
    "atendente_destino_nome": "Maria",
    "motivo": "Cliente solicitou especialista",
    "criado_em": "2025-10-11T21:00:00Z"
  }
}
```

#### Avaliar Atendimento
```http
POST /api/v1/atendimento/atendimentos/{id}/avaliar/

{
  "avaliacao": 5,
  "comentario": "Excelente atendimento!"
}
```

---

## 🔔 Notificações e Presença

### Preferências de Notificação

#### Obter Preferências
```http
GET /api/v1/me/preferencias-notificacao/
Authorization: Bearer {token}
```

**Resposta:**
```json
{
  "id": 1,
  "som_nova_mensagem": true,
  "som_novo_atendimento": true,
  "som_transferencia": true,
  "desktop_nova_mensagem": true,
  "desktop_novo_atendimento": true,
  "mostrar_badge_mensagens": true,
  "modo_nao_perturbe": false,
  "nao_perturbe_inicio": null,
  "nao_perturbe_fim": null,
  "esta_em_nao_perturbe": false
}
```

#### Atualizar Preferências
```http
PATCH /api/v1/me/preferencias-notificacao/

{
  "modo_nao_perturbe": true,
  "nao_perturbe_inicio": "22:00:00",
  "nao_perturbe_fim": "08:00:00"
}
```

---

### Presença de Agente

#### Meu Status
```http
GET /api/v1/presence/me/
Authorization: Bearer {token}
```

**Resposta:**
```json
{
  "id": 1,
  "agent": 5,
  "agent_username": "joao",
  "status": "online",
  "status_message": "Disponível",
  "is_available": true,
  "tempo_no_status_atual": 15,
  "websocket_connected": true
}
```

#### Alterar Status
```http
POST /api/v1/presence/set-status/

{
  "status": "busy",
  "message": "Em reunião até 15h"
}
```

**Status Disponíveis**: `online`, `offline`, `busy`, `away`

#### Heartbeat (Manter Vivo)
```http
POST /api/v1/presence/heartbeat/
Authorization: Bearer {token}
```

Deve ser chamado a cada 30 segundos para manter status online.

---

### Indicadores de Digitação

#### Indicar que Está Digitando
```http
POST /api/v1/typing/

{
  "chat_id": "5511999999999"
}
```

#### Parar de Digitar
```http
DELETE /api/v1/typing/?chat_id=5511999999999
```

---

## ⚙️ Configurações

### Obter Todas as Configurações
```http
GET /api/v1/config/
Authorization: Bearer {token}
```

### Configuração da Empresa
```http
GET /api/v1/config/company/
PATCH /api/v1/config/company/

{
  "nome": "DX Connect",
  "cnpj": "12345678000190",
  "telefone": "11999999999",
  "email": "contato@dxconnect.com.br"
}
```

### Configuração de Chat
```http
GET /api/v1/config/chat/
PATCH /api/v1/config/chat/

{
  "timeout_inatividade_minutos": 30,
  "mensagem_boas_vindas": "Olá! Como posso ajudar?",
  "mensagem_ausente": "No momento não há atendentes disponíveis."
}
```

### Templates de Documentos
```http
GET /api/v1/config/
```

Retorna `document_templates` com templates de contratos e boletos.

---

## 🌐 WebSocket

### Conexão

```javascript
const token = 'seu-jwt-token';
const ws = new WebSocket(`ws://localhost:8001/ws/whatsapp/?token=${token}`);
```

### Eventos Recebidos

Ver documentação completa em: **[`docs/NOTIFICATION_EVENTS.md`](./NOTIFICATION_EVENTS.md)**

#### Principais Eventos:

**message_received** - Nova mensagem recebida
**message_sent** - Mensagem enviada com sucesso
**chat_assigned** - Novo atendimento atribuído
**chat_transferred** - Atendimento transferido
**chat_auto_closed** - Encerramento automático
**agent_presence_changed** - Mudança de status de agente
**typing_start** / **typing_stop** - Indicadores de digitação
**session_status** - Status da sessão WhatsApp
**qrcode** - QR Code para autenticação

### Exemplo de Listener

```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.event) {
    case 'message_received':
      handleNewMessage(data.data);
      playSound('new_message.mp3');
      showNotification('Nova mensagem', data.data.message);
      break;
      
    case 'chat_assigned':
      handleNewChat(data.data);
      playSound('new_chat.mp3');
      break;
      
    case 'qrcode':
      displayQRCode(data.data.image_b64);
      break;
      
    case 'typing_start':
      showTypingIndicator(data.data.chat_id, data.data.from);
      break;
  }
};
```

### Ping/Pong (Keep Alive)

```javascript
// Enviar ping a cada 30s
setInterval(() => {
  ws.send(JSON.stringify({type: 'ping'}));
}, 30000);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'pong') {
    console.log('Connection alive');
  }
};
```

---

## 📊 Estrutura de Resposta Padrão

### Sucesso (200, 201)
```json
{
  "id": 1,
  "campo": "valor",
  ...
}
```

### Lista Paginada
```json
{
  "count": 100,
  "next": "http://localhost:8001/api/v1/clientes/?page=2",
  "previous": null,
  "results": [...]
}
```

### Erro (400, 404, 500)
```json
{
  "error": "Mensagem de erro",
  "detail": "Detalhes adicionais"
}
```

### Erro de Validação (400)
```json
{
  "campo": ["Este campo é obrigatório"],
  "outro_campo": ["Formato inválido"]
}
```

---

## 🔗 Links Úteis

- **Swagger UI**: http://localhost:8001/api/docs/
- **ReDoc**: http://localhost:8001/api/redoc/
- **Schema JSON**: http://localhost:8001/api/schema/

---

## 📚 Documentações Detalhadas

- [WhatsApp - Sessões e Eventos](./WHATSAPP_SESSION_EVENTS.md)
- [Eventos de Notificação WebSocket](./NOTIFICATION_EVENTS.md)
- [Integração CEP](./CEP_INTEGRATION.md)
- [Configuração CORS](./CORS_CONFIGURATION.md)
- [Variáveis de Ambiente](./ENVIRONMENT_VARIABLES.md)

---

**Atualizado em**: 12 de Outubro de 2025
**Versão da API**: v1

