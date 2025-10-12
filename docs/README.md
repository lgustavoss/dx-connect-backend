# 📚 Documentação - DX Connect Backend

## 🎯 Para Desenvolvedores Frontend

### 🚀 Início Rápido
1. **[Frontend Quickstart](./FRONTEND_QUICKSTART.md)** ⭐ **COMECE AQUI**
   - Setup inicial
   - Autenticação
   - WebSocket
   - Exemplos de código

2. **[API Reference](./API_REFERENCE.md)** 📘 **REFERÊNCIA COMPLETA**
   - Todos os endpoints
   - Exemplos de request/response
   - Códigos de status
   - Filtros e paginação

3. **[WebSocket Events](./NOTIFICATION_EVENTS.md)** 🔌 **EVENTOS EM TEMPO REAL**
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

**Última Atualização**: 12 de Outubro de 2025  
**Versão da API**: v1  
**Sprint Atual**: Sprint 4 (Qualidade)
