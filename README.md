# DX Connect - Backend API

API backend para o sistema de gestão e atendimento ao cliente DX Connect.

## 🛠️ Stack Tecnológica

- **Language:** Python 3.11+
- **Framework:** Django 4.2+
- **API Framework:** Django REST Framework (DRF)
- **Database:** PostgreSQL
- **Authentication:** JWT (Simple JWT)
- **Container:** Docker

## 🚀 Como Executar (Desenvolvimento)

1.  Clone o repositório:
    ```bash
    git clone https://github.com/seu-usuario/dx-connect-backend.git
    cd dx-connect-backend
    ```

2.  Configure o ambiente:
    ```bash
    cp .env.example .env
    # Edite o arquivo .env com suas configurações
    ```

3.  Inicie os containers:
    ```bash
    docker-compose up -d
    ```

4.  Execute as migrações:
    ```bash
    docker-compose exec web python manage.py migrate
    ```

5.  (Opcional) Execute os testes:
    ```bash
    docker-compose exec web python manage.py test
    ```

## 🧪 Testes

### Executar Testes

```bash
# Executar todos os testes
docker-compose exec web python manage.py test

# Executar testes de um app específico
docker-compose exec web python manage.py test accounts

# Executar testes com verbose
docker-compose exec web python manage.py test -v 2
```

### Cobertura de Código

```bash
# Executar testes com cobertura
docker-compose exec web python -m coverage run --source='.' manage.py test

# Ver relatório de cobertura no terminal
docker-compose exec web python -m coverage report

# Gerar relatório HTML
docker-compose exec web python -m coverage html

# Abrir relatório HTML (após gerar)
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

### Estrutura dos Testes

Os testes estão organizados por app:

- `accounts/tests/` - Testes do modelo Agent e views de autenticação/autorização
- `core/tests/` - Testes do modelo Config, views de configuração e WhatsApp

### Cobertura Atual

- **Total:** 59.04%
- **Models:** 100% (Agent), 39% (Config)
- **Views/APIs:** 100% (accounts), 38% (core config), 51% (WhatsApp)
- **Utils:** 17% (core/utils.py)
- **Validators:** 21% (core/validators.py)
- **Crypto:** 33% (core/crypto.py)
- **WebSocket:** 0% (core/ws.py)
- **Integrations:** 98% (whatsapp_stub.py)

### Metas de Cobertura

- **Models:** ≥90%
- **APIs:** ≥80%
- **Total:** ≥85%

## 📋 Endpoints da API

### Base

- Ambiente local (containers):
  - Base URL: `http://localhost:8001`
  - Versão da API: `http://localhost:8001/api/v1`

### Health Check
- Método: `GET`
- URL: `/api/v1/health/`
- Autenticação: não requerida
- Exemplo:
  ```bash
  curl -sS http://localhost:8001/api/v1/health/
  ```

### Autenticação (JWT - SimpleJWT)

1) Obter Token
- Método: `POST`
- URL: `/api/v1/auth/token/`
- Body (JSON):
  ```json
  { "username": "admin", "password": "admin" }
  ```
- Resposta (200):
  ```json
  { "refresh": "<refresh_token>", "access": "<access_token>" }
  ```

2) Renovar Token
- Método: `POST`
- URL: `/api/v1/auth/refresh/`
- Body (JSON):
  ```json
  { "refresh": "<refresh_token>" }
  ```
- Resposta (200):
  ```json
  { "access": "<access_token>" }
  ```

### Usuário Atual (Protegido)
- Método: `GET`
- URL: `/api/v1/me/`
- Autenticação: `Authorization: Bearer <access_token>`
- Exemplo:
  ```bash
  curl -H "Authorization: Bearer <access>" http://localhost:8001/api/v1/me/
  ```

### Documentação da API
- Swagger UI: `http://localhost:8001/api/docs/`
- Redoc: `http://localhost:8001/api/redoc/`
- OpenAPI Schema (JSON): `http://localhost:8001/api/schema/`

Validação recomendada (frontend-first):
- Testes via Postman/Insomnia (coleção em `.postman/`)
- Evitar depender do Django Admin para validação de features

## 📚 Diretrizes de API (Guidelines)

- Versão: prefixo `/api/v1` em todos os endpoints
- Paginação: PageNumberPagination (query params: `page`, `page_size`; padrão 20, máx. 100)
- Idempotência: requisições que podem ser repetidas devem retornar identificadores estáveis (ex.: `message_id`)
- Cache: usar cache curto (ex.: 30s) para listas estáveis quando aplicável

## 🔌 WebSocket (Base)

- Servidor: ASGI (Daphne) + Django Channels
- Autenticação: JWT via query string no handshake
  - Exemplo de URL (local):
    - `ws://localhost:8001/ws/echo/?token=<ACCESS_TOKEN>`
- Ping/Pong:
  - Envie: `{ "type": "ping" }`
  - Resposta: `{ "type": "pong" }`


## 📲 Sessão WhatsApp (Stub)

- Driver: stub interno para desenvolvimento/CI (sem integração externa)
- Endpoints REST:
  - POST `/api/v1/whatsapp/session/start` → 202 { status }
  - GET `/api/v1/whatsapp/session/status` → 200 { status }
  - DELETE `/api/v1/whatsapp/session` → 204
  - POST `/api/v1/whatsapp/messages` → 202 { message_id }
- WebSocket:
  - Rota: `ws://localhost:8001/ws/whatsapp/?token=<ACCESS_TOKEN>`
  - Eventos emitidos:
    - `session_status` (connecting, qrcode, authenticated, ready, disconnected)
    - `qrcode` (image_b64)
    - `message_status` (queued, sent, delivered, read, failed)
    - `message_received` (payload inbound simulado)
- Permissões: endpoints protegidos por `core.manage_config_whatsapp`.
- Variáveis de ambiente úteis:
  - `WHATSAPP_STUB_FAST=1` (torna transições imediatas em dev/CI)

Exemplo rápido (curl):
```bash
# obter token
ACCESS=$(curl -s -X POST http://localhost:8001/api/v1/auth/token/ -H 'Content-Type: application/json' -d '{"username":"admin","password":"admin"}' | jq -r .access)

# iniciar sessão
curl -i -X POST http://localhost:8001/api/v1/whatsapp/session/start -H "Authorization: Bearer $ACCESS"

# consultar status
curl -s http://localhost:8001/api/v1/whatsapp/session/status -H "Authorization: Bearer $ACCESS"

# enviar mensagem
curl -s -X POST http://localhost:8001/api/v1/whatsapp/messages -H 'Content-Type: application/json' -H "Authorization: Bearer $ACCESS" \
  -d '{"to":"5599999999999","type":"text","text":"Olá"}'
```

Teste rápido do WS (wscat):
```bash
npx wscat -c "ws://localhost:8001/ws/whatsapp/?token=$ACCESS"
```

## 🧪 Testes

### Django Test Runner
```bash
docker compose exec web python manage.py test core.tests.test_whatsapp_session -v 2
```

### Newman (Postman) via Docker
```bash
# executa pastas 07 e 08 da coleção
docker compose run --rm newman
```

## ❗ Padrão de Erros (simplificado)

Formato base (RFC 7807-like):
```json
{
  "error": {
    "code": "INVALID_PAYLOAD",
    "message": "Campo 'to' é obrigatório",
    "details": { "to": ["Este campo é obrigatório."] },
    "request_id": "req-123",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

Exemplos de códigos: `INVALID_PAYLOAD`, `UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND`, `RATE_LIMITED`, `UPSTREAM_ERROR`, `INTERNAL_ERROR`.

## 📦 Contratos (exemplos)

- Envio WhatsApp (POST) retorna `202 Accepted` com `message_id` para enfileiramento
- Eventos em tempo real: payloads versionados com `version: v1`

Para contratos completos, consulte o schema OpenAPI em `/api/schema/` e os exemplos nos endpoints do Swagger/Redoc.
