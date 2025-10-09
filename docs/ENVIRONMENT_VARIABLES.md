# Variáveis de Ambiente - DX Connect Backend

## 📋 Visão Geral

Este documento descreve todas as variáveis de ambiente necessárias para configurar o backend do DX Connect.

## 🚀 Configuração Rápida

1. Copie o template `.env.example` para `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edite o arquivo `.env` com seus valores específicos

3. Reinicie os containers Docker:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## 📚 Variáveis por Categoria

### Django Core

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `DJANGO_ENV` | Ambiente de execução | `development` | Não |
| `SECRET_KEY` | Chave secreta do Django | - | ✅ Sim |
| `DEBUG` | Modo debug | `True` | Não |
| `ALLOWED_HOSTS` | Hosts permitidos (separados por vírgula) | `localhost,127.0.0.1` | ✅ Sim |

**Exemplo**:
```env
DJANGO_ENV=development
SECRET_KEY=django-insecure-your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
```

---

### CORS - Cross-Origin Resource Sharing

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `CORS_ALLOWED_ORIGINS` | Origens permitidas para CORS (separadas por vírgula) | - | ✅ Sim |

**Desenvolvimento**:
```env
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

**Produção**:
```env
CORS_ALLOWED_ORIGINS=https://app.dxconnect.com,https://www.dxconnect.com
```

**⚠️ IMPORTANTE**: 
- **NUNCA** use `CORS_ALLOW_ALL_ORIGINS=True` em produção
- `CORS_ALLOW_CREDENTIALS` deve permanecer `False` (padrão) para JWT via headers
- Use origens específicas (sem wildcards) em produção

---

### Database - PostgreSQL

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `POSTGRES_DB` | Nome do banco de dados | `dxconnect` | ✅ Sim |
| `POSTGRES_USER` | Usuário do banco | `dxconnect_user` | ✅ Sim |
| `POSTGRES_PASSWORD` | Senha do banco | - | ✅ Sim |
| `POSTGRES_HOST` | Host do banco | `db` | ✅ Sim |
| `POSTGRES_PORT` | Porta do banco | `5432` | ✅ Sim |

**Exemplo**:
```env
POSTGRES_DB=dxconnect
POSTGRES_USER=dxconnect_user
POSTGRES_PASSWORD=strong-password-here
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

---

### Redis - Cache e Channels

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `REDIS_HOST` | Host do Redis | `redis` | ✅ Sim |
| `REDIS_PORT` | Porta do Redis | `6379` | ✅ Sim |
| `REDIS_DB` | Número do banco Redis | `0` | Não |

**Exemplo**:
```env
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
```

---

### JWT - Autenticação

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `JWT_ACCESS_TOKEN_LIFETIME` | Tempo de expiração do access token (minutos) | `60` | Não |
| `JWT_REFRESH_TOKEN_LIFETIME` | Tempo de expiração do refresh token (dias) | `7` | Não |
| `JWT_ALGORITHM` | Algoritmo de assinatura | `HS256` | Não |

**Exemplo**:
```env
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=7
JWT_ALGORITHM=HS256
```

---

### Email - SMTP

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `EMAIL_HOST` | Servidor SMTP | - | Não |
| `EMAIL_PORT` | Porta SMTP | `587` | Não |
| `EMAIL_USE_TLS` | Usar TLS | `True` | Não |
| `EMAIL_HOST_USER` | Usuário SMTP | - | Não |
| `EMAIL_HOST_PASSWORD` | Senha SMTP | - | Não |
| `DEFAULT_FROM_EMAIL` | Email remetente padrão | - | Não |

**Exemplo (Gmail)**:
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@dxconnect.com
```

**Desenvolvimento** (usar console):
```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

---

### WhatsApp - Integração

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `WHATSAPP_MODE` | Modo de operação (`stub` ou `production`) | `stub` | Não |
| `WHATSAPP_STUB_FAST` | Velocidade do stub (0=lento, 1=rápido) | `1` | Não |

**Desenvolvimento**:
```env
WHATSAPP_MODE=stub
WHATSAPP_STUB_FAST=1
```

**Produção** (descomente quando configurar):
```env
WHATSAPP_MODE=production
WHATSAPP_API_URL=https://api.whatsapp.com
WHATSAPP_API_TOKEN=your-api-token
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your-verify-token
```

---

### Celery - Tarefas Assíncronas

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `CELERY_BROKER_URL` | URL do broker (Redis) | - | Não |
| `CELERY_RESULT_BACKEND` | Backend de resultados | - | Não |
| `CELERY_TIMEZONE` | Timezone do Celery | `America/Sao_Paulo` | Não |

**Exemplo**:
```env
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/1
CELERY_TIMEZONE=America/Sao_Paulo
```

---

### Storage - Arquivos e Mídia

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `STORAGE_BACKEND` | Backend de storage (`local` ou `s3`) | `local` | Não |

**Desenvolvimento**:
```env
STORAGE_BACKEND=local
```

**Produção com S3** (descomente quando configurar):
```env
STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=dxconnect-media
AWS_S3_REGION_NAME=us-east-1
```

---

### Logging

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `LOG_LEVEL` | Nível de log | `INFO` | Não |
| `LOG_FORMAT` | Formato de log (`json` ou `text`) | `json` | Não |

**Exemplo**:
```env
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

### Sentry - Monitoramento (Produção)

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `SENTRY_DSN` | DSN do Sentry | - | Não |
| `SENTRY_ENVIRONMENT` | Ambiente do Sentry | - | Não |
| `SENTRY_TRACES_SAMPLE_RATE` | Taxa de amostragem de traces | `0.1` | Não |

**Produção**:
```env
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

---

### Segurança (Produção)

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `SECURE_SSL_REDIRECT` | Redirecionar para HTTPS | `False` | Não |
| `SECURE_HSTS_SECONDS` | Tempo HSTS (segundos) | `0` | Não |
| `SESSION_COOKIE_SECURE` | Cookie de sessão seguro | `False` | Não |
| `CSRF_COOKIE_SECURE` | Cookie CSRF seguro | `False` | Não |

**Produção**:
```env
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

---

### Performance

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `WEB_CONCURRENCY` | Número de workers | `4` | Não |
| `WEB_TIMEOUT` | Timeout para requisições (segundos) | `30` | Não |

**Exemplo**:
```env
WEB_CONCURRENCY=4
WEB_TIMEOUT=30
```

---

## 🔒 Segurança

### ⚠️ NUNCA faça:

- ❌ Commitar o arquivo `.env` com valores reais
- ❌ Usar `DEBUG=True` em produção
- ❌ Usar `CORS_ALLOW_ALL_ORIGINS=True` em produção
- ❌ Usar senhas fracas
- ❌ Compartilhar `SECRET_KEY` ou tokens

### ✅ SEMPRE faça:

- ✅ Use valores fortes para `SECRET_KEY` e senhas
- ✅ Configure `CORS_ALLOWED_ORIGINS` com domínios específicos
- ✅ Habilite HTTPS em produção
- ✅ Use um gerenciador de secrets (AWS Secrets Manager, Vault, etc)
- ✅ Configure monitoramento de erros (Sentry)
- ✅ Mantenha as variáveis de ambiente atualizadas

---

## 📝 Gerando Valores Seguros

### Secret Key do Django:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Senha Forte:
```bash
openssl rand -base64 32
```

---

## 🔗 Referências

- [Django Settings](https://docs.djangoproject.com/en/4.2/ref/settings/)
- [Django CORS Headers](https://github.com/adamchainz/django-cors-headers)
- [12 Factor App - Config](https://12factor.net/config)
- [OWASP Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Django_REST_Framework_Cheat_Sheet.html)

