# Configuração CORS - DX Connect Backend

## 📋 Visão Geral

Esta documentação descreve como o CORS (Cross-Origin Resource Sharing) está configurado no backend do DX Connect para permitir requisições do frontend com autenticação JWT via headers.

## 🎯 Objetivo

Permitir que o frontend (rodando em diferentes origens) faça requisições para a API do backend incluindo o header `Authorization` com tokens JWT, **sem uso de cookies**.

## ⚙️ Configuração Atual

### Variáveis de Ambiente

```env
# Desenvolvimento
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Produção (exemplo)
CORS_ALLOWED_ORIGINS=https://app.dxconnect.com,https://www.dxconnect.com
```

### Django Settings (config/settings/base.py)

```python
# Origens permitidas (configuradas via variável de ambiente)
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])

# Fallback para desenvolvimento (se não houver origins configuradas)
if not CORS_ALLOWED_ORIGINS and DEBUG:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:5173",  # Vite
        "http://127.0.0.1:5173",
        "http://localhost:3000",  # React/Next.js
        "http://127.0.0.1:3000",
    ]

# JWT via headers → SEM cookies/credenciais
CORS_ALLOW_CREDENTIALS = False

# Headers permitidos (inclui 'authorization' para JWT)
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",  # Essencial para JWT
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# Métodos HTTP permitidos
CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]
```

### Middleware

O middleware CORS **DEVE** estar na primeira posição:

```python
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # PRIMEIRO!
    "django.middleware.security.SecurityMiddleware",
    # ... outros middlewares
]
```

## 🧪 Testes

### 1. Testar Requisição OPTIONS (Preflight)

```powershell
# PowerShell
Invoke-WebRequest -Method OPTIONS `
  -Uri "http://localhost:8001/api/v1/auth/token/" `
  -Headers @{
    "Origin"="http://localhost:5173";
    "Access-Control-Request-Method"="POST";
    "Access-Control-Request-Headers"="authorization,content-type"
  } `
  -UseBasicParsing
```

**Resposta Esperada:**
```
StatusCode: 200
Headers:
  Access-Control-Allow-Origin: http://localhost:5173
  Access-Control-Allow-Headers: authorization, content-type, ...
  Access-Control-Allow-Methods: DELETE, GET, OPTIONS, PATCH, POST, PUT
  Access-Control-Allow-Credentials: (vazio ou ausente)
```

### 2. Testar Requisição Real com JWT

```powershell
# 1. Obter token
$response = Invoke-WebRequest -Method POST `
  -Uri "http://localhost:8001/api/v1/auth/token/" `
  -Headers @{"Origin"="http://localhost:5173"} `
  -Body '{"username":"admin","password":"admin"}' `
  -ContentType "application/json" `
  -UseBasicParsing

$token = ($response.Content | ConvertFrom-Json).access

# 2. Usar token em requisição autenticada
Invoke-WebRequest -Method GET `
  -Uri "http://localhost:8001/api/v1/me/" `
  -Headers @{
    "Origin"="http://localhost:5173";
    "Authorization"="Bearer $token"
  } `
  -UseBasicParsing
```

**Resposta Esperada:**
```
StatusCode: 200
Headers:
  Access-Control-Allow-Origin: http://localhost:5173
```

### 3. Testar Origem Não Permitida

```powershell
Invoke-WebRequest -Method OPTIONS `
  -Uri "http://localhost:8001/api/v1/auth/token/" `
  -Headers @{
    "Origin"="http://malicious-site.com";
    "Access-Control-Request-Method"="POST"
  } `
  -UseBasicParsing
```

**Resposta Esperada:**
```
StatusCode: 200
Headers:
  Access-Control-Allow-Origin: (ausente ou vazio)
```

## ✅ Checklist de Validação

- [x] Middleware CORS está na primeira posição
- [x] `CORS_ALLOW_CREDENTIALS = False` (JWT via headers)
- [x] Headers incluem `authorization`
- [x] Requisição OPTIONS retorna 200
- [x] Header `Access-Control-Allow-Origin` está presente para origens permitidas
- [x] Header `Access-Control-Allow-Credentials` está ausente ou False
- [x] Origens não permitidas não recebem headers CORS

## 🔒 Segurança

### ✅ Boas Práticas Implementadas

1. **CORS_ALLOW_CREDENTIALS = False**: Essencial para JWT via headers (sem cookies)
2. **Origins Específicas**: Apenas origins configuradas são permitidas
3. **Fallback Seguro**: Em produção, se `CORS_ALLOWED_ORIGINS` estiver vazio, **nenhuma** origem será permitida
4. **Headers Explícitos**: Lista específica de headers permitidos
5. **Middleware na Primeira Posição**: Garante que CORS seja processado antes de qualquer outra lógica

### ❌ O que NÃO Fazer

1. **NUNCA** use `CORS_ALLOW_ALL_ORIGINS = True` em produção
2. **NUNCA** use `CORS_ALLOW_CREDENTIALS = True` com JWT em header
3. **NUNCA** use wildcards em `CORS_ALLOWED_ORIGINS` (ex: `*.example.com`)
4. **NUNCA** deixe `CORS_ALLOWED_ORIGINS` vazio em produção

## 🌐 Configuração por Ambiente

### Desenvolvimento

```env
DJANGO_DEBUG=True
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

**Comportamento**: Se `CORS_ALLOWED_ORIGINS` não estiver configurada E `DEBUG=True`, usa fallback para localhost.

### Staging

```env
DJANGO_DEBUG=False
CORS_ALLOWED_ORIGINS=https://staging.dxconnect.com
ALLOWED_HOSTS=staging.dxconnect.com,api-staging.dxconnect.com
```

### Produção

```env
DJANGO_DEBUG=False
CORS_ALLOWED_ORIGINS=https://app.dxconnect.com,https://www.dxconnect.com
ALLOWED_HOSTS=app.dxconnect.com,api.dxconnect.com
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
```

## 🐛 Troubleshooting

### Problema: "CORS policy: No 'Access-Control-Allow-Origin' header is present"

**Causa**: A origem não está na lista de `CORS_ALLOWED_ORIGINS`.

**Solução**:
1. Verifique a origem do frontend (URL completa, incluindo porta)
2. Adicione a origem em `CORS_ALLOWED_ORIGINS` no arquivo `.env`
3. Reinicie o backend: `docker-compose restart web`

### Problema: "CORS policy: The value of the 'Access-Control-Allow-Credentials' header is ''"

**Causa**: Conflito entre `CORS_ALLOW_CREDENTIALS` e autenticação.

**Solução**: Mantenha `CORS_ALLOW_CREDENTIALS = False` e use JWT via header `Authorization` (não em cookies).

### Problema: Requisições OPTIONS retornam 403/405

**Causa**: Middleware CORS não está na primeira posição.

**Solução**: Verifique que `CorsMiddleware` está no topo da lista de `MIDDLEWARE`.

### Problema: Headers customizados não são permitidos

**Causa**: Header não está em `CORS_ALLOW_HEADERS`.

**Solução**: Adicione o header customizado em `CORS_ALLOW_HEADERS` no `settings/base.py`.

## 📊 Fluxo de Requisição CORS

```
1. Frontend (http://localhost:5173) faz requisição OPTIONS
   ↓
2. CorsMiddleware verifica se origem está em CORS_ALLOWED_ORIGINS
   ↓
3. Se permitida, adiciona headers CORS à resposta:
   - Access-Control-Allow-Origin: http://localhost:5173
   - Access-Control-Allow-Headers: authorization, content-type, ...
   - Access-Control-Allow-Methods: GET, POST, PUT, ...
   ↓
4. Browser permite requisição real (POST, GET, etc)
   ↓
5. Frontend envia requisição com header Authorization: Bearer {token}
   ↓
6. Backend processa e retorna resposta com headers CORS
```

## 🔗 Referências

- [Django CORS Headers](https://github.com/adamchainz/django-cors-headers)
- [MDN - CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
- [OWASP CORS Security](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html#cross-origin-resource-sharing)

## 📝 Changelog

### v1.0.0 (Issue #27)
- Configuração inicial de CORS para integração com frontend
- Suporte a JWT via headers (sem cookies)
- Fallback seguro para desenvolvimento
- Documentação completa
- Testes de validação

