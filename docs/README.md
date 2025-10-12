# 📚 Documentação - DX Connect Backend

## 🎯 Para Desenvolvedores Frontend

### 🚀 Início Rápido
1. **[Frontend API Guide](./FRONTEND_API_GUIDE.md)** ⭐ **COMECE AQUI**
   - Setup completo com React/Vue/JS
   - Autenticação JWT + Refresh
   - Exemplos de código prontos
   - Hooks e serviços reutilizáveis

2. **[Frontend Quickstart](./FRONTEND_QUICKSTART.md)** 🏃 **GUIA RÁPIDO**
   - Setup inicial em 5 minutos
   - Conexão WebSocket
   - Primeiro request

3. **[API Reference](./API_REFERENCE.md)** 📘 **REFERÊNCIA COMPLETA**
   - Todos os endpoints documentados
   - Exemplos de request/response
   - Códigos de status
   - Filtros e paginação

4. **[Lista Completa de Endpoints](./API_ENDPOINTS_COMPLETE.md)** 📋 **ÍNDICE RÁPIDO**
   - 93 endpoints organizados
   - Tabela de referência rápida
   - Indicadores de autenticação
   - Quick start examples

5. **[WebSocket Events](./NOTIFICATION_EVENTS.md)** 🔌 **EVENTOS EM TEMPO REAL**
   - Protocolo de eventos v1
   - Payloads completos
   - Preferências de notificação
   - Implementação frontend

---

## 📖 Guias por Funcionalidade

### WhatsApp
- **[WhatsApp - Sessões e Eventos](./WHATSAPP_SESSION_EVENTS.md)**
  - Gerenciamento de sessões
  - Envio/recebimento de mensagens
  - Processamento de mídias
  - Métricas de latência
  - Reconexão automática

- **[Guia de Testes com Stub](./WHATSAPP_STUB_TESTING.md)** 🧪
  - Como testar sem WhatsApp real
  - Simular conversas completas
  - Injetar mensagens de teste
  - Classe JavaScript pronta
  - Troubleshooting

- **[API de Chats](./CHATS_API.md)** 💬 **NOVO**
  - Listagem de conversas agrupadas
  - Histórico isolado por atendimento
  - Auto-criação de atendimentos
  - Aceitar, transferir e encerrar chats
  - Alertas de novos chats

### Clientes e Documentos
- **[Documentos e Contratos](./ISSUE_35_DOCUMENTOS.md)**
  - Geração automática de contratos
  - Templates configuráveis
  - Substituição de variáveis

### Integrações
- **[Integração CEP](./CEP_INTEGRATION.md)**
  - Busca de endereço por CEP
  - Cache automático
  - Tratamento de erros

---

## ⚙️ Configuração e Deploy

### Ambiente
- **[Variáveis de Ambiente](./ENVIRONMENT_VARIABLES.md)**
  - Todas as variáveis disponíveis
  - Configurações por ambiente
  - Valores padrão

- **[Configuração CORS](./CORS_CONFIGURATION.md)**
  - Setup para desenvolvimento
  - Configuração de produção
  - Troubleshooting

### Deploy
- **[Guia Rápido de Deploy](./QUICK_DEPLOY_GUIDE.md)** (10min)
- **[Guia Completo de Deploy](./DEPLOY.md)**
- **[Checklist Pós-Deploy](./POST_DEPLOY_CHECKLIST.md)**

---

## 🎯 Documentação por Sprint

### Sprint 1 - Núcleo do Sistema ✅
- WebSocket base
- Configurações seguras
- CORS
- Deploy

### Sprint 2 - Gestão de Pessoas ✅
- Clientes CRUD
- Contatos
- Documentos/Contratos ([Docs](./ISSUE_35_DOCUMENTOS.md))
- Integração CEP ([Docs](./CEP_INTEGRATION.md))

### Sprint 3 - Atendimento via Chat ✅
- WhatsApp completo ([Docs](./WHATSAPP_SESSION_EVENTS.md))
- Filas de atendimento
- Transferências
- Notificações ([Docs](./NOTIFICATION_EVENTS.md))
- Presença de agentes
- Encerramento automático

---

## 🔗 Links Rápidos

### APIs Interativas
- **Swagger UI**: http://localhost:8001/api/docs/
- **ReDoc**: http://localhost:8001/api/redoc/
- **Schema OpenAPI**: http://localhost:8001/api/schema/

### Admin Django
- **Admin Panel**: http://localhost:8001/admin/

### Health Check
- **Health**: http://localhost:8001/api/v1/health/

---

## 📊 Estrutura de Endpoints

```
/api/v1/
├── auth/
│   ├── token/              # Login (obter JWT)
│   └── refresh/            # Refresh token
├── me/                     # Dados do usuário
│   └── preferencias-notificacao/  # Preferências
├── presence/               # Presença de agentes
│   ├── me/                 # Meu status
│   ├── set-status/         # Alterar status
│   └── heartbeat/          # Keep alive
├── typing/                 # Indicadores de digitação
├── clientes/               # Gestão de clientes
├── contatos/               # Contatos de clientes
├── grupos-empresa/         # Grupos de empresa
├── documentos/             # Documentos e contratos
├── whatsapp/               # Sistema WhatsApp
│   ├── sessions/           # Sessões
│   ├── messages/           # Mensagens
│   ├── send/               # Enviar mensagem
│   └── webhook/            # Webhook externo
├── atendimento/            # Sistema de atendimento
│   ├── departamentos/      # Departamentos
│   ├── filas/              # Filas de espera
│   └── atendimentos/       # Atendimentos ativos
├── integrations/
│   └── cep/                # Busca de CEP
└── config/                 # Configurações
    ├── company/
    ├── chat/
    ├── email/
    ├── appearance/
    └── whatsapp/
```

---

## 🔌 WebSocket

```
ws://localhost:8001/ws/
├── whatsapp/              # Eventos WhatsApp e atendimento
└── echo/                  # Teste de conexão
```

**Autenticação**: `?token={jwt_token}`

---

## 📝 Status do Projeto

| Sprint | Status | Issues | Conclusão |
|--------|--------|--------|-----------|
| Sprint 1 - Núcleo | ✅ Completa | 4/4 | 100% |
| Sprint 2 - Gestão | ✅ Completa | 4/4 | 100% |
| Sprint 3 - Atendimento | ✅ Completa | 10/10 | 100% |
| Sprint 4 - Qualidade | ⏳ Planejada | 5/5 | 0% |

**Total de Issues**: 24 implementadas
**Taxa de Testes**: 95% (309 testes)
**Linhas de Código**: ~11.500

---

## 🆘 Precisa de Ajuda?

### Documentação
1. Leia o [API Reference](./API_REFERENCE.md)
2. Veja o [Frontend Quickstart](./FRONTEND_QUICKSTART.md)
3. Explore o Swagger UI
4. Consulte os guias específicos

### Testes
```bash
# Testar endpoints
docker-compose logs -f web

# Ver estrutura no Swagger
http://localhost:8001/api/docs/
```

---

---

## 📦 Documentos Disponíveis

| Documento | Descrição | Ideal Para |
|-----------|-----------|------------|
| [Frontend API Guide](./FRONTEND_API_GUIDE.md) | Guia prático com código React/Vue/JS | Frontend Dev (Setup completo) |
| [Frontend Quickstart](./FRONTEND_QUICKSTART.md) | Início rápido em 5 minutos | Frontend Dev (Quick start) |
| [API Reference](./API_REFERENCE.md) | Referência completa de endpoints | Todos |
| [API Endpoints Complete](./API_ENDPOINTS_COMPLETE.md) | Lista de 93 endpoints | Referência rápida |
| [WhatsApp Session Events](./WHATSAPP_SESSION_EVENTS.md) | Eventos e métricas WhatsApp | Frontend + Backend |
| [WhatsApp Stub Testing](./WHATSAPP_STUB_TESTING.md) | Como testar sem WhatsApp real | QA + Frontend |
| [Notification Events](./NOTIFICATION_EVENTS.md) | Protocolo WebSocket v1 | Frontend Dev |
| [CEP Integration](./CEP_INTEGRATION.md) | Integração ViaCEP | Frontend + Backend |
| [CORS Configuration](./CORS_CONFIGURATION.md) | Setup CORS | DevOps |
| [Environment Variables](./ENVIRONMENT_VARIABLES.md) | Variáveis de ambiente | DevOps |
| [Quick Deploy Guide](./QUICK_DEPLOY_GUIDE.md) | Deploy em 10 minutos | DevOps |
| [Deploy Guide](./DEPLOY.md) | Deploy completo | DevOps |
| [Post Deploy Checklist](./POST_DEPLOY_CHECKLIST.md) | Checklist pós-deploy | DevOps |
| [Issue 35 - Documentos](./ISSUE_35_DOCUMENTOS.md) | Geração de contratos | Backend Dev |
| [Status do Projeto](./STATUS_PROJETO.md) | Status geral do projeto | PM + Tech Lead |

**Total**: 15 documentos | **Páginas**: ~200 | **Exemplos de código**: 100+

---

**Última Atualização**: 12 de Outubro de 2025  
**Versão da API**: v1  
**Sprint Atual**: Sprint 4 (Qualidade)  
**Documentação**: ✅ 100% Atualizada
