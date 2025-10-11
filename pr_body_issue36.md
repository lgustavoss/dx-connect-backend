# PR: WhatsApp - Sessões e Eventos (Issue #36)

## 📋 Descrição

Implementação completa do sistema de gerenciamento de sessões WhatsApp Web com persistência em banco de dados e métricas de latência em tempo real.

Fecha #36

---

## ✨ Funcionalidades Implementadas

### 1. **Modelos de Persistência**
- ✅ `WhatsAppSession`: Gerenciamento completo de sessões WhatsApp
  - Estados (disconnected, connecting, qrcode, authenticated, ready, error)
  - Métricas (mensagens enviadas/recebidas, uptime, erros)
  - Métodos auxiliares (mark_as_connected, mark_as_disconnected, etc)
  
- ✅ `WhatsAppMessage`: Histórico completo de mensagens
  - Suporte para múltiplos tipos (text, image, audio, video, document, etc)
  - Rastreamento de status (queued → sent → delivered → read)
  - Cálculo automático de latência em milissegundos

### 2. **Serviço de Gestão**
- ✅ `WhatsAppSessionService`: Camada de integração entre stub e persistência
  - Iniciar/parar sessões
  - Enviar mensagens com persistência automática
  - Receber e processar mensagens
  - Atualizar status de mensagens
  - Thread-safe para operações assíncronas

### 3. **Endpoints REST API**
- ✅ **Sessões** (`/api/v1/whatsapp/sessions/`)
  - `POST /start/`: Iniciar sessão
  - `POST /stop/`: Encerrar sessão
  - `GET /status/`: Consultar status
  - `GET /{id}/metrics/`: Métricas detalhadas da sessão
  - Filtros: status, is_active
  - Busca: phone_number, device_name

- ✅ **Mensagens** (`/api/v1/whatsapp/messages/`)
  - `GET /`: Listar mensagens (paginado)
  - `GET /{id}/`: Detalhar mensagem
  - `GET /high-latency/`: Mensagens com latência > 5s
  - `GET /latency-stats/`: Estatísticas agregadas de latência
  - Filtros: direction, message_type, status, chat_id, session
  - Busca: text_content, contact_number, contact_name

- ✅ **Envio de Mensagens** (`/api/v1/whatsapp/send/`)
  - Suporte para texto e mídia
  - Validação de dados
  - ID customizado para rastreamento

### 4. **WebSocket Aprimorado**
- ✅ Consumer com persistência automática
  - Recebe eventos do serviço stub
  - Persiste mensagens no banco em tempo real
  - Envia eventos para o cliente
  - Suporte a injeção de mensagens para testes

### 5. **Métricas de Latência**
- ✅ Cálculo automático em milissegundos
- ✅ Propriedades calculadas:
  - `latency_to_sent_ms`: Até envio
  - `latency_to_delivered_ms`: Até entrega
  - `latency_to_read_ms`: Até leitura
  - `total_latency_ms`: Latência total
  - `is_latency_acceptable`: Verifica se < 5s
- ✅ Logs automáticos para latências altas
- ✅ Endpoints de estatísticas

### 6. **Admin Django**
- ✅ Interface administrativa completa
- ✅ Filtros e busca
- ✅ Visualização de métricas

---

## 📂 Arquivos Criados

### App WhatsApp
```
whatsapp/
├── __init__.py
├── apps.py
├── models.py              # WhatsAppSession, WhatsAppMessage
├── serializers.py         # Serializers DRF
├── views.py              # ViewSets e views
├── urls.py               # Rotas do app
├── admin.py              # Configuração do Django Admin
├── service.py            # WhatsAppSessionService
├── consumers.py          # WhatsAppConsumer (WebSocket)
├── migrations/
│   └── 0001_initial.py
└── tests/
    ├── __init__.py
    ├── test_models.py        # Testes dos modelos
    ├── test_views.py         # Testes das views
    └── test_integration.py   # Testes de integração
```

### Documentação
```
docs/
└── WHATSAPP_SESSION_EVENTS.md  # Documentação completa
```

---

## 🔄 Arquivos Modificados

### Configuração
- `config/settings/base.py`: Adicionado `whatsapp` ao `INSTALLED_APPS`
- `config/urls.py`: Incluído `whatsapp.urls`

---

## 🧪 Testes

### Cobertura
- ✅ **40 testes** implementados
- ✅ **100% de sucesso**
- ✅ Cobertura completa:
  - Modelos (CRUD, propriedades, métodos)
  - Serializers
  - Views (endpoints, filtros, permissões)
  - Serviços (sessões, mensagens)
  - Integração (ciclo completo)

### Executar Testes
```bash
docker-compose exec web python manage.py test whatsapp
```

---

## 📊 Modelos

### WhatsAppSession

| Campo | Tipo | Descrição |
|-------|------|-----------|
| usuario | FK | Usuário responsável |
| status | CharField | Status da sessão |
| device_name | CharField | Nome do dispositivo |
| phone_number | CharField | Número do WhatsApp |
| connected_at | DateTime | Data/hora da conexão |
| total_messages_sent | Integer | Total enviadas |
| total_messages_received | Integer | Total recebidas |
| error_count | Integer | Contador de erros |

**Propriedades:**
- `is_connected`: Verifica se está pronta
- `uptime_seconds`: Tempo de atividade

### WhatsAppMessage

| Campo | Tipo | Descrição |
|-------|------|-----------|
| session | FK | Sessão associada |
| message_id | CharField | ID único |
| direction | CharField | inbound/outbound |
| message_type | CharField | text, image, audio, etc |
| contact_number | CharField | Número do contato |
| text_content | TextField | Conteúdo de texto |
| status | CharField | queued, sent, delivered, read |
| queued_at | DateTime | Data/hora de criação |
| sent_at | DateTime | Data/hora de envio |
| delivered_at | DateTime | Data/hora de entrega |
| read_at | DateTime | Data/hora de leitura |

**Propriedades:**
- `latency_to_sent_ms`: Latência até envio
- `latency_to_delivered_ms`: Latência até entrega
- `total_latency_ms`: Latência total
- `is_latency_acceptable`: Verifica se < 5000ms

---

## 🔌 Exemplos de Uso

### Iniciar Sessão
```bash
curl -X POST http://localhost:8001/api/v1/whatsapp/sessions/start/ \
  -H "Authorization: Bearer $TOKEN"
```

### Enviar Mensagem
```bash
curl -X POST http://localhost:8001/api/v1/whatsapp/send/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "5511999999999",
    "type": "text",
    "text": "Olá! Como posso ajudar?"
  }'
```

### WebSocket
```javascript
const token = 'your-jwt-token';
const ws = new WebSocket(`ws://localhost:8001/ws/whatsapp/?token=${token}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Evento:', data);
};
```

---

## 📈 Métricas de Latência

### Critérios
- ✅ **Latência Aceitável**: < 5 segundos (5000ms)
- ❌ **Latência Alta**: ≥ 5 segundos

### Logs Automáticos
- **INFO**: Mensagens com latência aceitável
- **WARNING**: Mensagens com latência alta (> 5s)

### Estatísticas
```bash
GET /api/v1/whatsapp/messages/latency-stats/
```

Retorna:
- Total de mensagens
- Latência média de envio
- Latência média de entrega
- Taxa de latência aceitável
- Quantidade de mensagens > 5s

---

## 🗄️ Migrations

```bash
# Criar tabelas
docker-compose exec web python manage.py migrate
```

**Migrations criadas:**
- `whatsapp/migrations/0001_initial.py`
  - Tabela `whatsapp_whatsappsession`
  - Tabela `whatsapp_whatsappmessage`
  - Índices otimizados para queries

---

## 📝 Checklist

- [x] Modelos criados e testados
- [x] Serializers implementados
- [x] Views e endpoints criados
- [x] Serviço de gestão implementado
- [x] WebSocket consumer aprimorado
- [x] Métricas de latência funcionando
- [x] Admin configurado
- [x] Testes unitários (100% sucesso)
- [x] Testes de integração (100% sucesso)
- [x] Documentação completa
- [x] Migrations geradas
- [x] URLs registradas

---

## 🎯 Critérios de Aceitação (Issue #36)

- [x] ✅ Gerenciar sessão (iniciar/parar/estado)
- [x] ✅ Receber mensagens com log de latência < 5s
- [x] ✅ Persistência mínima de histórico
- [x] ✅ Serviço de sessão implementado
- [x] ✅ Modelos de mensagem criados
- [x] ✅ Endpoints funcionando
- [x] ✅ Métricas de latência implementadas

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

### 3. Verificar Health
```bash
curl http://localhost:8001/api/v1/health/
```

---

## 📚 Documentação

Documentação completa disponível em:
- **`docs/WHATSAPP_SESSION_EVENTS.md`**

Inclui:
- Visão geral das funcionalidades
- Descrição detalhada dos modelos
- Referência completa dos endpoints
- Guia de uso do WebSocket
- Exemplos práticos em Python e JavaScript
- Informações sobre métricas de latência

---

## 🔗 Referências

- **Issue**: #36 - WhatsApp Web - sessão e eventos (latência < 5s)
- **Sprint**: 3 - Atendimento via Chat
- **Milestone**: Sprint 3

---

## 🎉 Próximos Passos

Com a Issue #36 concluída, o próximo passo é:

1. **Issue #44**: WhatsApp: Recebimento de Mensagens (webhook)
2. **Issue #45**: WhatsApp: Envio de Mensagens (fila)
3. **Issue #46**: WhatsApp: Processamento de Mídias
4. **Issue #47**: WhatsApp: Gestão de Sessões e Conexão (avançado)

---

**Desenvolvido com ❤️ para o DX Connect**

