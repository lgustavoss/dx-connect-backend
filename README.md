# DX Connect - Backend API

API backend para o sistema de gestão e atendimento ao cliente DX Connect.

## 🛠️ Stack Tecnológica

- **Language:** Python 3.11+
- **Framework:** Django 4.2+
- **API Framework:** Django REST Framework (DRF)
- **Database:** PostgreSQL
- **Authentication:** JWT (Simple JWT)
- **Container:** Docker

## 🚀 Como Executar

### Desenvolvimento Local

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/seu-usuario/dx-connect-backend.git
   cd dx-connect-backend
   ```

2. **Configure o ambiente:**
   ```bash
   cp .env.example .env
   # Edite o arquivo .env com suas configurações
   ```

3. **Inicie os containers:**
   ```bash
   docker-compose up -d
   ```

4. **Execute as migrações:**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

5. **Crie um superusuário (opcional):**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

6. **Execute os testes:**
   ```bash
   docker-compose exec web python manage.py test
   ```

### Script de Inicialização Rápida

Para facilitar o setup inicial, use o script `docker-run.sh`:

```bash
# Build e start dos containers
./docker-run.sh build
./docker-run.sh start

# Na primeira execução, execute as migrações
./docker-run.sh migrate

# Crie um superusuário
./docker-run.sh createsuperuser
```

### Verificação da Instalação

Após a inicialização, verifique se tudo está funcionando:

```bash
# Health check
curl http://localhost:8001/api/v1/health/

# Teste de autenticação
curl -X POST http://localhost:8001/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

### Deploy em Produção

**📚 Guias de Deploy Disponíveis**:
- 🚀 **[Guia Rápido (10min)](docs/QUICK_DEPLOY_GUIDE.md)** - Deploy rápido em produção
- 📖 **[Guia Completo](docs/DEPLOY.md)** - Documentação detalhada de deploy
- ✅ **[Checklist Pós-Deploy](docs/POST_DEPLOY_CHECKLIST.md)** - Validação após deploy

**⚡ Deploy Rápido**:
```bash
# 1. Configurar ambiente
cp .env.example .env.production
nano .env.production  # Configure SECRET_KEY, ALLOWED_HOSTS, etc

# 2. Deploy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# 3. Validar
bash scripts/validate_deploy.sh
```

Para instruções detalhadas, consulte [Deploy em Produção](#-deploy-em-produção).

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

## 🚀 Deploy em Produção

### Pré-requisitos

- Docker e Docker Compose instalados
- Domínio configurado (ex: `api.seudominio.com`)
- Certificado SSL (recomendado: Let's Encrypt)
- Banco de dados PostgreSQL (pode ser o mesmo container ou externo)
- Redis (pode ser o mesmo container ou externo)

### Configuração de Produção

1. **Configure as variáveis de ambiente:**
   ```bash
   cp .env.example .env.production
   # Edite .env.production com valores de produção
   ```

2. **Principais configurações para produção:**
   ```bash
   DEBUG=False
   SECRET_KEY=your-very-secure-secret-key-here
   ALLOWED_HOSTS=api.seudominio.com,www.seudominio.com
   DB_PASSWORD=your-secure-database-password
   EMAIL_HOST_PASSWORD=your-secure-email-password
   ```

3. **Use o docker-compose de produção:**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

### Script de Deploy

```bash
#!/bin/bash
# deploy.sh

echo "🚀 Iniciando deploy do DX Connect Backend..."

# Pull das últimas mudanças
git pull origin main

# Build das imagens
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Parar containers existentes
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# Iniciar novos containers
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Executar migrações
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py migrate

# Coletar arquivos estáticos (se necessário)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

echo "✅ Deploy concluído!"
```

### Monitoramento

- **Health Check:** `https://api.seudominio.com/api/v1/health/`
- **Logs:** `docker-compose logs -f web`
- **Métricas:** Use ferramentas como Prometheus + Grafana

### Backup

```bash
# Backup do banco de dados
docker-compose exec db pg_dump -U dxconnect dxconnect > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup dos arquivos de mídia
tar -czf media_backup_$(date +%Y%m%d_%H%M%S).tar.gz media/
```

### Troubleshooting

- **Container não inicia:** Verifique logs com `docker-compose logs web`
- **Erro de migração:** Execute `docker-compose exec web python manage.py migrate --fake-initial`
- **Problemas de permissão:** Verifique ownership dos arquivos com `ls -la`
