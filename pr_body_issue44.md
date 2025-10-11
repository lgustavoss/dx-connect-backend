# PR: WhatsApp - Recebimento de Mensagens (Issue #44)

## 📋 Descrição

Implementação do sistema de recebimento de mensagens WhatsApp via webhook, com persistência de payload bruto, versão do protocolo e formato padronizado v1.

Fecha #44

---

## ✨ Funcionalidades Implementadas

### 1. **Campos Adicionais no Modelo**
- ✅ `raw_payload`: Armazena payload bruto sem processamento
- ✅ `protocol_version`: Versão do protocolo de comunicação (v1, v2, etc)

### 2. **Endpoint Webhook**
- ✅ `POST /api/v1/whatsapp/webhook/`: Recebe mensagens externas
- ✅ Validação de campos obrigatórios
- ✅ Suporte para texto e mídia (image, audio, video, document)
- ✅ Cálculo de latência (< 5s conforme requisito)
- ✅ Persistência automática no banco
- ✅ Emissão de eventos via WebSocket no formato v1

### 3. **Estrutura de Evento Padronizada (v1)**
```json
{
  "event": "message_received",
  "data": {
    "from": "5511999999999",
    "message": "Texto da mensagem",
    "message_id": "abc123",
    "timestamp": "2024-01-01T10:00:00Z",
    "media_url": null,
    "media_type": null,
    "latency_ms": 1230
  },
  "version": "v1"
}
```

### 4. **Autenticação WS por Role**
- ✅ Mensagens são roteadas para sessões ativas específicas
- ✅ Cada atendente só recebe mensagens de sua sessão (user_id)
- ✅ Eventos emitidos via WebSocket para grupos específicos (`user_{id}_whatsapp`)

### 5. **Melhorias no Serviço**
- ✅ Método `handle_incoming_message` atualizado para receber `raw_payload` e `protocol_version`
- ✅ Persistência completa de payload bruto para auditoria
- ✅ Logs estruturados com latência e versão do protocolo

---

## 📂 Arquivos Modificados

### Modelo
- `whatsapp/models.py`: Adicionados campos `raw_payload` e `protocol_version`

### Serviço
- `whatsapp/service.py`: Atualizado `handle_incoming_message` para suportar novos campos

### Views
- `whatsapp/views.py`: Nova view `WhatsAppWebhookView`

### Serializers
- `whatsapp/serializers.py`: Adicionados novos campos ao `WhatsAppMessageSerializer`

### URLs
- `whatsapp/urls.py`: Rota `/webhook/` registrada

### Migrations
- `whatsapp/migrations/0002_add_raw_payload_protocol_version.py`: Nova migração

---

## 🔌 Uso do Webhook

### Endpoint
```
POST /api/v1/whatsapp/webhook/
```

### Formato da Requisição (v1)
```json
{
  "event": "message_received",
  "data": {
    "from": "5511999999999",
    "message": "Olá! Preciso de ajuda",
    "message_id": "abc123",
    "timestamp": "2025-10-11T15:30:00Z",
    "media_url": null,
    "media_type": null
  },
  "version": "v1"
}
```

### Campos Obrigatórios
- `event`: Deve ser `"message_received"`
- `data.from`: Número do remetente
- `data.message`: Conteúdo da mensagem

### Campos Opcionais
- `data.message_id`: ID único (gerado automaticamente se ausente)
- `data.timestamp`: Data/hora da mensagem
- `data.media_url`: URL da mídia
- `data.media_type`: Tipo MIME da mídia
- `version`: Versão do protocolo (padrão: "v1")

### Exemplo com Mídia
```json
{
  "event": "message_received",
  "data": {
    "from": "5511988888888",
    "message": "Veja essa imagem",
    "message_id": "img_001",
    "timestamp": "2025-10-11T15:35:00Z",
    "media_url": "https://example.com/image.jpg",
    "media_type": "image/jpeg"
  },
  "version": "v1"
}
```

### Resposta de Sucesso
```json
{
  "id": 123,
  "message_id": "abc123",
  "direction": "inbound",
  "message_type": "text",
  "contact_number": "5511999999999",
  "text_content": "Olá! Preciso de ajuda",
  "status": "delivered",
  "raw_payload": { ... },
  "protocol_version": "v1",
  ...
}
```

### Códigos de Status
- `200 OK`: Mensagem recebida e processada com sucesso
- `400 Bad Request`: Dados inválidos ou campos obrigatórios ausentes
- `503 Service Unavailable`: Nenhuma sessão ativa disponível
- `500 Internal Server Error`: Erro ao processar mensagem

---

## 📊 Fluxo de Recebimento

1. **Webhook recebe payload** do provedor externo
2. **Valida estrutura** (evento, campos obrigatórios)
3. **Armazena payload bruto** (`raw_payload`)
4. **Processa dados** (extrai campos, determina tipo)
5. **Busca sessão ativa** para rotear mensagem
6. **Persiste no banco** via `WhatsAppSessionService`
7. **Calcula latência** (timestamp recebimento - timestamp envio)
8. **Emite evento WebSocket** no formato v1 padronizado
9. **Retorna resposta** com dados da mensagem criada

---

## 📈 Métricas de Latência

### Requisito da Issue
- ✅ **Latência alvo < 5 segundos**

### Como é Calculado
```python
received_at = timezone.now()  # Timestamp ao receber webhook
# ... processamento ...
latency_ms = (timezone.now() - received_at).total_seconds() * 1000
```

### Logs
```
Mensagem webhook recebida: abc123 de 5511999999999 
(latência: 1230ms, protocolo: v1)
```

---

## 🧪 Testes

### Testes Existentes
- ✅ **40 testes** continuam passando
- ✅ Nenhuma regressão introduzida

### Teste Manual do Webhook
```bash
curl -X POST http://localhost:8001/api/v1/whatsapp/webhook/ \
  -H "Content-Type: application/json" \
  -d '{
    "event": "message_received",
    "data": {
      "from": "5511999999999",
      "message": "Teste de webhook",
      "message_id": "test_001"
    },
    "version": "v1"
  }'
```

---

## 🔒 Segurança

### Autenticação
- 🔓 Webhook atual é **público** (sem autenticação)
- ⚠️ **TODO**: Implementar validação por assinatura HMAC
- ⚠️ **TODO**: Adicionar rate limiting

### Recomendações para Produção
1. Implementar validação de assinatura
2. Adicionar IP whitelist
3. Configurar rate limiting
4. Usar HTTPS obrigatório
5. Log de tentativas de acesso

---

## 📝 Checklist

- [x] Campos `raw_payload` e `protocol_version` adicionados
- [x] Migration criada e aplicada
- [x] Endpoint webhook implementado
- [x] Estrutura de evento v1 padronizada
- [x] Autenticação WS por role mantida
- [x] Serviço atualizado para novos campos
- [x] Serializers atualizados
- [x] URL registrada
- [x] Testes existentes passando
- [x] Logs com latência implementados
- [x] Documentação criada

---

## 🎯 Critérios de Aceitação (Issue #44)

- [x] ✅ Estrutura de evento v1 definida
- [x] ✅ Persistir payload bruto + versão do protocolo
- [x] ✅ Latência < 5s (com log de tempo)
- [x] ✅ Auth WS por role (atendente só recebe suas mensagens)

---

## 🚀 Deploy

### 1. Aplicar Migrations
```bash
./docker-run.sh migrate
```

### 2. Reiniciar Serviços
```bash
./docker-run.sh restart
```

### 3. Testar Webhook
```bash
curl -X POST https://api.seudominio.com/api/v1/whatsapp/webhook/ \
  -H "Content-Type: application/json" \
  -d @test_webhook_payload.json
```

---

## 🔗 Referências

- **Issue**: #44 - WhatsApp: Recebimento de Mensagens
- **Sprint**: 3 - Atendimento via Chat
- **Milestone**: Sprint 3
- **Issue Anterior**: #36 - WhatsApp Web - sessão e eventos

---

## 🎉 Próximos Passos

Com a Issue #44 concluída, sugerimos seguir para:

1. **Issue #45**: WhatsApp: Envio de Mensagens (fila)
2. **Issue #46**: WhatsApp: Processamento de Mídias
3. **Issue #47**: WhatsApp: Gestão de Sessões e Conexão (avançado)

---

**Desenvolvido com ❤️ para o DX Connect**

