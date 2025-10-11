# PR: Filas de Atendimento por Departamento (Issue #37)

## 📋 Descrição

Implementação completa de sistema de filas de atendimento com distribuição automática, priorização e balanceamento de carga entre atendentes.

Fecha #37

---

## ✨ Funcionalidades Implementadas

### 1. **Novo App `atendimento`**
Sistema completo de gerenciamento de filas e atendimentos.

### 2. **Modelos**

#### Departamento
- Organização por áreas (Vendas, Suporte, Financeiro, etc)
- Atendentes vinculados por departamento
- Configurações: max atendimentos simultâneos, SLA de resposta
- Método `get_atendentes_disponiveis()` para balanceamento

#### FilaAtendimento
- Fila de espera por departamento
- Priorização (baixa, normal, alta, urgente)
- Ordenação: Prioridade DESC + FIFO
- Métricas de tempo de espera

#### Atendimento
- Chat ativo entre atendente e cliente
- Estados: aguardando, em_atendimento, pausado, finalizado, cancelado
- Métricas: tempo primeira resposta, duração total
- Contadores de mensagens
- Sistema de avaliação (1-5 estrelas)

### 3. **Serviço de Distribuição Automática**
`DistribuicaoAtendimentoService` implementa:
- ✅ Atribuição automática ao atendente disponível
- ✅ Balanceamento de carga (round-robin)
- ✅ Respeita capacidade máxima por atendente
- ✅ Priorização (urgente > alta > normal > baixa)
- ✅ FIFO dentro da mesma prioridade
- ✅ Atribuição manual opcional

### 4. **Endpoints REST API**

Base URL: `/api/v1/atendimento/`

#### Departamentos
- `GET /departamentos/`: Listar departamentos
- `POST /departamentos/`: Criar departamento
- `GET /departamentos/{id}/`: Detalhar
- `PATCH /departamentos/{id}/`: Atualizar
- `DELETE /departamentos/{id}/`: Remover

#### Filas
- `GET /filas/`: Listar filas pendentes
- `POST /filas/`: Adicionar cliente na fila
- `POST /filas/distribuir/`: Forçar distribuição automática

#### Atendimentos
- `GET /atendimentos/`: Listar atendimentos
- `GET /atendimentos/meus-atendimentos/`: Atendimentos ativos do usuário
- `POST /atendimentos/{id}/finalizar/`: Finalizar atendimento
- `POST /atendimentos/{id}/avaliar/`: Adicionar avaliação

---

## 📊 Fluxo de Atendimento

```
1. Cliente envia mensagem WhatsApp
    ↓
2. Identifica departamento (Vendas, Suporte, etc)
    ↓
3. Adiciona na fila (POST /filas/)
    ↓
4. Distribuição automática dispara
    ↓
5. Busca atendentes disponíveis
    ↓
6. Atribui ao atendente com menos carga
    ↓
7. Cria Atendimento (status: em_atendimento)
    ↓
8. Notifica atendente via WebSocket
    ↓
9. Atendente responde
    ↓
10. Finaliza atendimento
    ↓
11. Cliente avalia (opcional)
```

---

## 🎯 Distribuição Automática

### Algoritmo
1. Busca filas pendentes ordenadas por prioridade + FIFO
2. Busca atendentes disponíveis do departamento
3. Filtra atendentes com capacidade (< max simultâneos)
4. Atribui ao atendente com menos atendimentos ativos
5. Cria registro de Atendimento
6. Marca fila como atribuída
7. Repete até acabar fila ou atendentes

### Exemplo
```
Departamento: Suporte
Max simultâneos: 5

Fila:
1. Cliente A (urgente) - 5 min esperando
2. Cliente B (alta) - 10 min esperando
3. Cliente C (normal) - 15 min esperando

Atendentes:
- João (2 atendimentos ativos) ← escolhido primeiro
- Maria (3 atendimentos ativos)
- Pedro (5 atendimentos ativos) ← não disponível

Resultado:
- Cliente A → João
- Cliente B → Maria  
- Cliente C → João (ainda tem capacidade)
```

---

## 🔢 Prioridades

### Níveis
| Prioridade | Ordem | Exemplo |
|------------|-------|---------|
| **Urgente** | 1 | Cliente VIP, problema crítico |
| **Alta** | 2 | Cliente insatisfeito |
| **Normal** | 3 | Atendimento padrão |
| **Baixa** | 4 | Dúvida simples |

### Ordenação
```sql
ORDER BY prioridade DESC, entrou_na_fila_em ASC
```

---

## 📡 Uso da API

### Adicionar na Fila
```bash
curl -X POST http://localhost:8001/api/v1/atendimento/filas/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "departamento": 1,
    "cliente": 5,
    "chat_id": "5511999999999",
    "numero_whatsapp": "5511999999999",
    "mensagem_inicial": "Preciso de ajuda com...",
    "prioridade": "alta"
  }'
```

### Distribuir Automaticamente
```bash
curl -X POST http://localhost:8001/api/v1/atendimento/filas/distribuir/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "departamento_id": 1
  }'
```

**Resposta:**
```json
{
  "message": "3 atendimentos distribuídos",
  "distribuidos": 3
}
```

### Meus Atendimentos
```bash
curl http://localhost:8001/api/v1/atendimento/atendimentos/meus-atendimentos/ \
  -H "Authorization: Bearer $TOKEN"
```

### Finalizar Atendimento
```bash
curl -X POST http://localhost:8001/api/v1/atendimento/atendimentos/1/finalizar/ \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "observacoes": "Cliente satisfeito, problema resolvido"
  }'
```

---

## 🎯 Critérios de Aceitação (Issue #37)

- [x] ✅ Modelo de fila e regras básicas
- [x] ✅ Atribuição automática ao atendente disponível
- [x] ✅ Modelos criados
- [x] ✅ Serviços de distribuição
- [x] ✅ Endpoints implementados

---

## 📝 Checklist

- [x] App `atendimento` criado
- [x] Modelo Departamento
- [x] Modelo FilaAtendimento
- [x] Modelo Atendimento
- [x] DistribuicaoAtendimentoService
- [x] Serializers DRF
- [x] ViewSets e endpoints
- [x] Admin Django
- [x] URLs registradas
- [x] Migration gerada
- [x] Documentação criada

---

## 🚀 Deploy

### 1. Aplicar Migration
```bash
docker-compose exec web python manage.py migrate
```

### 2. Criar Departamentos Iniciais
```python
from atendimento.models import Departamento

Departamento.objects.create(
    nome="Vendas",
    descricao="Atendimento comercial",
    cor="#10B981",
    max_atendimentos_simultaneos=3
)

Departamento.objects.create(
    nome="Suporte",
    descricao="Suporte técnico",
    cor="#3B82F6",
    max_atendimentos_simultaneos=5
)
```

---

## 🔗 Referências

- **Issue**: #37 - Filas de Atendimento por Departamento
- **Sprint**: 3 - Atendimento via Chat

---

**Desenvolvido com ❤️ para o DX Connect**

