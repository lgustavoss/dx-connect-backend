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
