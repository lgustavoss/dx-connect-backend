# Eventos WebSocket de Notificação (Issue #39)

## 📋 Protocolo de Eventos v1

Todos os eventos seguem o formato padronizado:
```json
{
  "event": "nome_do_evento",
  "data": { ... },
  "version": "v1"
}
```

---

## 🔔 Eventos Disponíveis

### 1. **message_received** (Nova Mensagem)
Disparado quando uma nova mensagem é recebida.

```json
{
  "event": "message_received",
  "data": {
    "from": "5511999999999",
    "message": "Olá! Preciso de ajuda",
    "message_id": "abc123",
    "timestamp": "2025-10-11T20:00:00Z",
    "media_url": null,
    "media_type": null,
    "latency_ms": 123
  },
  "version": "v1"
}
```

**Notificação:**
- 🔊 Som: Se `preferencias.som_nova_mensagem = true`
- 🖥️ Desktop: Se `preferencias.desktop_nova_mensagem = true`
- 🔴 Badge: Incrementa contador de mensagens

---

### 2. **chat_assigned** (Novo Atendimento Atribuído)
Disparado quando um atendimento é atribuído ao atendente.

```json
{
  "event": "chat_assigned",
  "data": {
    "atendimento_id": 123,
    "cliente_nome": "Empresa XYZ Ltda",
    "chat_id": "5511999999999",
    "departamento": "Suporte",
    "prioridade": "alta",
    "mensagem_inicial": "Preciso de ajuda urgente...",
    "timestamp": "2025-10-11T20:00:00Z"
  },
  "version": "v1"
}
```

**Notificação:**
- 🔊 Som: Se `preferencias.som_novo_atendimento = true`
- 🖥️ Desktop: Se `preferencias.desktop_novo_atendimento = true`
- 🔴 Badge: Incrementa contador de atendimentos

---

### 3. **chat_transferred** (Atendimento Transferido)
Disparado quando um atendimento é transferido para o atendente.

```json
{
  "event": "chat_transferred",
  "data": {
    "atendimento_id": 123,
    "cliente_nome": "Empresa XYZ",
    "chat_id": "5511999999999",
    "de": "João Silva",
    "motivo": "Cliente solicitou especialista",
    "timestamp": "2025-10-11T20:00:00Z"
  },
  "version": "v1"
}
```

**Notificação:**
- 🔊 Som: Se `preferencias.som_transferencia = true`
- 🖥️ Desktop: Se `preferencias.desktop_transferencia = true`
- 🔴 Badge: Incrementa contador

---

### 4. **message_sent** (Confirmação de Envio)
Disparado quando uma mensagem é enviada com sucesso.

```json
{
  "event": "message_sent",
  "data": {
    "message_id": "xyz789",
    "status": "queued",
    "to": "5511999999999",
    "timestamp": "2025-10-11T20:00:00Z",
    "error": null
  },
  "version": "v1"
}
```

**Notificação:**
- ℹ️ Apenas visual (sem som)

---

### 5. **chat_auto_closed** (Encerramento Automático)
Disparado quando um atendimento é encerrado por inatividade.

```json
{
  "event": "chat_auto_closed",
  "data": {
    "atendimento_id": 123,
    "cliente_nome": "Empresa XYZ",
    "chat_id": "5511999999999",
    "motivo": "inatividade",
    "tempo_inativo_minutos": 45,
    "timestamp": "2025-10-11T20:00:00Z"
  },
  "version": "v1"
}
```

**Notificação:**
- ℹ️ Apenas informativo

---

### 6. **typing_start** / **typing_stop** (Digitando)
Indicadores de digitação em tempo real.

```json
{
  "event": "typing_start",
  "data": {
    "chat_id": "5511999999999",
    "from": "João Silva",
    "timestamp": "2025-10-11T20:00:00Z"
  },
  "version": "v1"
}
```

**Notificação:**
- ℹ️ Visual apenas (indicador de digitação)

---

## ⚙️ Preferências de Notificação

### Endpoint
`GET/PATCH /api/v1/me/preferencias-notificacao/`

### Obter Preferências
```bash
curl http://localhost:8001/api/v1/me/preferencias-notificacao/ \
  -H "Authorization: Bearer $TOKEN"
```

### Atualizar Preferências
```bash
curl -X PATCH http://localhost:8001/api/v1/me/preferencias-notificacao/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "som_nova_mensagem": true,
    "som_novo_atendimento": true,
    "desktop_nova_mensagem": true,
    "modo_nao_perturbe": true,
    "nao_perturbe_inicio": "22:00:00",
    "nao_perturbe_fim": "08:00:00"
  }'
```

---

## 🔕 Modo Não Perturbe

### Funcionamento
- Desabilita **TODAS** as notificações sonoras
- Notificações visuais continuam funcionando
- Pode ser configurado por horário

### Exemplo
```json
{
  "modo_nao_perturbe": true,
  "nao_perturbe_inicio": "22:00:00",
  "nao_perturbe_fim": "08:00:00"
}
```

**Resultado**: Sem sons entre 22h e 8h.

---

## 🎨 Implementação Frontend

### JavaScript (WebSocket)
```javascript
const ws = new WebSocket('ws://localhost:8001/ws/whatsapp/?token=' + token);

ws.onmessage = (event) => {
  const notification = JSON.parse(event.data);
  
  // Buscar preferências do usuário
  const prefs = getUserPreferences();
  
  switch(notification.event) {
    case 'message_received':
      if (prefs.som_nova_mensagem && !prefs.esta_em_nao_perturbe) {
        playSound('new_message.mp3');
      }
      if (prefs.desktop_nova_mensagem) {
        showDesktopNotification('Nova mensagem', notification.data.message);
      }
      if (prefs.mostrar_badge_mensagens) {
        incrementBadge('messages');
      }
      break;
      
    case 'chat_assigned':
      if (prefs.som_novo_atendimento && !prefs.esta_em_nao_perturbe) {
        playSound('new_chat.mp3');
      }
      if (prefs.desktop_novo_atendimento) {
        showDesktopNotification('Novo atendimento', notification.data.cliente_nome);
      }
      break;
      
    case 'chat_transferred':
      if (prefs.som_transferencia && !prefs.esta_em_nao_perturbe) {
        playSound('transfer.mp3');
      }
      if (prefs.desktop_transferencia) {
        showDesktopNotification('Chat transferido', notification.data.cliente_nome);
      }
      break;
  }
};
```

---

## 📊 Resumo de Campos

| Campo | Tipo | Padrão | Descrição |
|-------|------|--------|-----------|
| `som_nova_mensagem` | Boolean | true | Som ao receber mensagem |
| `som_novo_atendimento` | Boolean | true | Som ao receber atendimento |
| `som_transferencia` | Boolean | true | Som ao receber transferência |
| `desktop_nova_mensagem` | Boolean | true | Notificação desktop mensagem |
| `desktop_novo_atendimento` | Boolean | true | Notificação desktop atendimento |
| `desktop_transferencia` | Boolean | true | Notificação desktop transferência |
| `mostrar_badge_mensagens` | Boolean | true | Badge de mensagens |
| `mostrar_badge_atendimentos` | Boolean | true | Badge de atendimentos |
| `modo_nao_perturbe` | Boolean | false | Desabilita sons |
| `nao_perturbe_inicio` | Time | null | Início do período |
| `nao_perturbe_fim` | Time | null | Fim do período |

---

## 🎯 Critérios de Aceitação (Issue #39)

- [x] ✅ Eventos WebSocket definidos
- [x] ✅ Preferências por usuário
- [x] ✅ Documentação de payloads completa
- [x] ✅ Modelo de preferências criado
- [x] ✅ Endpoints funcionando

---

**Desenvolvido com ❤️ para o DX Connect**

