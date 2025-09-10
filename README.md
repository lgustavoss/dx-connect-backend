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

(A documentação será incrementada aqui conforme o desenvolvimento.)
