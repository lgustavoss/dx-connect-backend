# PR: Notificações Sonoras/Visuais (Issue #39)

## 📋 Descrição

Sistema de preferências de notificação para atendentes com controle granular de alertas sonoros, visuais e modo não perturbe.

Fecha #39

---

## ✨ Funcionalidades Implementadas

### 1. **Modelo PreferenciasNotificacao**
Controle completo de notificações por usuário:
- ✅ Notificações sonoras (nova mensagem, novo atendimento, transferência)
- ✅ Notificações desktop/push
- ✅ Badges/contadores
- ✅ Modo Não Perturbe (com horário programável)

### 2. **Endpoints de Preferências**
- `GET /api/v1/me/preferencias-notificacao/`: Obter preferências
- `PATCH /api/v1/me/preferencias-notificacao/`: Atualizar preferências

### 3. **Eventos WebSocket Padronizados (v1)**
Todos os eventos implementados:
- `message_received` - Nova mensagem
- `chat_assigned` - Novo atendimento
- `chat_transferred` - Transferência
- `message_sent` - Confirmação de envio
- `chat_auto_closed` - Encerramento automático
- `typing_start` / `typing_stop` - Digitando

### 4. **Documentação Completa**
`docs/NOTIFICATION_EVENTS.md` com:
- Todos os payloads de eventos
- Exemplos de implementação frontend
- Configuração de preferências

---

## 📊 Preferências Disponíveis

### Notificações Sonoras
| Preferência | Padrão | Descrição |
|-------------|--------|-----------|
| `som_nova_mensagem` | ✅ true | Som ao receber mensagem |
| `som_novo_atendimento` | ✅ true | Som ao receber atendimento |
| `som_transferencia` | ✅ true | Som ao receber transferência |

### Notificações Desktop
| Preferência | Padrão | Descrição |
|-------------|--------|-----------|
| `desktop_nova_mensagem` | ✅ true | Notificação desktop mensagem |
| `desktop_novo_atendimento` | ✅ true | Notificação desktop atendimento |
| `desktop_transferencia` | ✅ true | Notificação desktop transferência |

### Badges
| Preferência | Padrão | Descrição |
|-------------|--------|-----------|
| `mostrar_badge_mensagens` | ✅ true | Badge contador mensagens |
| `mostrar_badge_atendimentos` | ✅ true | Badge contador atendimentos |

### Modo Não Perturbe
| Preferência | Padrão | Descrição |
|-------------|--------|-----------|
| `modo_nao_perturbe` | ❌ false | Ativar modo silencioso |
| `nao_perturbe_inicio` | null | Horário início (ex: 22:00) |
| `nao_perturbe_fim` | null | Horário fim (ex: 08:00) |

---

## 🔔 Exemplo de Uso

### Obter Preferências
```bash
curl http://localhost:8001/api/v1/me/preferencias-notificacao/ \
  -H "Authorization: Bearer $TOKEN"
```

**Resposta:**
```json
{
  "id": 1,
  "usuario": 5,
  "som_nova_mensagem": true,
  "som_novo_atendimento": true,
  "desktop_nova_mensagem": true,
  "mostrar_badge_mensagens": true,
  "modo_nao_perturbe": false,
  "esta_em_nao_perturbe": false
}
```

### Configurar Não Perturbe
```bash
curl -X PATCH http://localhost:8001/api/v1/me/preferencias-notificacao/ \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "modo_nao_perturbe": true,
    "nao_perturbe_inicio": "22:00:00",
    "nao_perturbe_fim": "08:00:00"
  }'
```

### Desabilitar Todos os Sons
```bash
curl -X PATCH http://localhost:8001/api/v1/me/preferencias-notificacao/ \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "som_nova_mensagem": false,
    "som_novo_atendimento": false,
    "som_transferencia": false
  }'
```

---

## 📂 Arquivos Criados

- `accounts/models_preferences.py`: Modelo PreferenciasNotificacao
- `accounts/serializers_preferences.py`: Serializer
- `accounts/views_preferences.py`: View de preferências
- `accounts/admin_preferences.py`: Admin
- `docs/NOTIFICATION_EVENTS.md`: Documentação completa

---

## 📂 Arquivos Modificados

- `accounts/models.py`: Import do modelo
- `config/urls.py`: Rota de preferências
- `accounts/migrations/0003_add_preferencias_notificacao.py`: Migration

---

## 🎯 Critérios de Aceitação (Issue #39)

- [x] ✅ Eventos WebSocket definidos
- [x] ✅ Preferências por usuário
- [x] ✅ Documentação de payloads
- [x] ✅ Modelo de preferências
- [x] ✅ Endpoints funcionando

---

## 🚀 Deploy

```bash
docker-compose exec web python manage.py migrate
```

---

## 🔗 Referências

- **Issue**: #39 - Notificações sonoras/visuais
- **Sprint**: 3
- **Documentação**: `docs/NOTIFICATION_EVENTS.md`

---

**Desenvolvido com ❤️ para o DX Connect**

