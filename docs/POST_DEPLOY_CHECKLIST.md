# ✅ Checklist Pós-Deploy - DX Connect Backend

## 📋 Verificações Obrigatórias

Execute este checklist após cada deploy em produção para garantir que tudo está funcionando corretamente.

---

## 🔍 1. Verificação de Serviços

### 1.1 Containers em Execução

```bash
docker-compose ps
```

**Esperado**: Todos os containers devem estar com status `Up` (healthy):
- ✅ `dxconnect_web` - Up (healthy)
- ✅ `dxconnect_db` - Up (healthy)
- ✅ `dxconnect_redis` - Up (healthy)
- ✅ `dxconnect_worker` - Up
- ✅ `dxconnect_beat` - Up
- ✅ `dxconnect_nginx` - Up (se usando)

### 1.2 Logs de Inicialização

```bash
docker-compose logs web --tail=50
```

**Esperado**:
- ✅ Sem erros críticos
- ✅ Mensagem: "Listening on TCP address 0.0.0.0:8000"
- ✅ Migrações aplicadas com sucesso
- ✅ Sem warnings de configuração

---

## 🌐 2. Endpoints da API

### 2.1 Health Check

```bash
curl -X GET https://api.seudominio.com/api/v1/health/
```

**Esperado**:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2025-10-09T20:00:00Z"
}
```

### 2.2 Autenticação JWT

```bash
# Obter token
curl -X POST https://api.seudominio.com/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"senha_forte"}'
```

**Esperado**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLC...",
  "refresh": "eyJ0eXAiOiJKV1QiLC..."
}
```

### 2.3 Endpoint Autenticado

```bash
# Usar o token obtido
curl -X GET https://api.seudominio.com/api/v1/me/ \
  -H "Authorization: Bearer {access_token}"
```

**Esperado**:
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  ...
}
```

---

## 🔒 3. Segurança

### 3.1 HTTPS

```bash
curl -I https://api.seudominio.com/api/v1/health/
```

**Verificar**:
- ✅ Status: 200 OK
- ✅ Header `Strict-Transport-Security` presente
- ✅ Header `X-Frame-Options: DENY`
- ✅ Header `X-Content-Type-Options: nosniff`

### 3.2 CORS

```bash
curl -X OPTIONS https://api.seudominio.com/api/v1/auth/token/ \
  -H "Origin: https://app.seudominio.com" \
  -H "Access-Control-Request-Method: POST" \
  -v
```

**Verificar**:
- ✅ Header `Access-Control-Allow-Origin: https://app.seudominio.com`
- ✅ Header `Access-Control-Allow-Headers` inclui `authorization`
- ✅ Header `Access-Control-Allow-Credentials` ausente ou `false`

### 3.3 Variáveis de Ambiente

```bash
docker-compose exec web env | grep DJANGO
```

**Verificar**:
- ✅ `DJANGO_DEBUG=False`
- ✅ `DJANGO_SECRET_KEY` está definida (não é padrão)
- ✅ `DJANGO_ALLOWED_HOSTS` contém o domínio correto

---

## 💾 4. Banco de Dados

### 4.1 Migrações

```bash
docker-compose exec web python manage.py showmigrations
```

**Esperado**: Todas as migrações com `[X]` (aplicadas)

### 4.2 Conexão

```bash
docker-compose exec db psql -U dxconnect -d dxconnect -c "SELECT version();"
```

**Esperado**: Retorna a versão do PostgreSQL

### 4.3 Backup Recente

```bash
ls -lh /opt/dx-connect/backups/ | tail -5
```

**Verificar**:
- ✅ Existe backup recente (últimas 24h)
- ✅ Tamanho do backup parece razoável (> 0 bytes)

---

## 📊 5. Performance

### 5.1 Tempo de Resposta

```bash
curl -w "\n\nTempo total: %{time_total}s\n" \
  -o /dev/null -s \
  https://api.seudominio.com/api/v1/health/
```

**Esperado**: Tempo < 1 segundo

### 5.2 Uso de Recursos

```bash
docker stats --no-stream
```

**Verificar**:
- ✅ Uso de CPU < 80%
- ✅ Uso de memória < 80%
- ✅ Sem containers em restart loop

---

## 🔔 6. WebSocket

### 6.1 Conexão WebSocket

```bash
# Testar com wscat (instalar: npm install -g wscat)
wscat -c "ws://api.seudominio.com/ws/echo/" \
  -H "Authorization: Bearer {access_token}"
```

**Esperado**: Conexão aceita e echo funcionando

---

## 📧 7. Email (Se Configurado)

### 7.1 Configuração SMTP

```bash
docker-compose exec web python manage.py shell -c "
from django.core.mail import send_mail
send_mail('Test', 'Mensagem de teste', 'noreply@seudominio.com', ['admin@seudominio.com'])
print('Email enviado com sucesso!')
"
```

**Esperado**: "Email enviado com sucesso!"

---

## 🔄 8. Celery (Tarefas Assíncronas)

### 8.1 Workers Ativos

```bash
docker-compose exec worker celery -A config inspect active
```

**Esperado**: Workers ativos e sem erros

### 8.2 Beat Schedulers

```bash
docker-compose exec beat celery -A config inspect scheduled
```

**Esperado**: Tarefas agendadas (se houver)

---

## 📱 9. WhatsApp Integration

### 9.1 Stub/Production Mode

```bash
docker-compose exec web env | grep WHATSAPP
```

**Verificar**:
- ✅ `WHATSAPP_MODE` está correto (`stub` para dev, `production` para prod)

---

## 📈 10. Monitoramento (Se Configurado)

### 10.1 Prometheus

```bash
curl -s http://localhost:9090/-/healthy
```

**Esperado**: "Prometheus is Healthy."

### 10.2 Grafana

```bash
curl -s http://localhost:3000/api/health
```

**Esperado**:
```json
{
  "database": "ok",
  "version": "..."
}
```

---

## 🎯 11. Funcionalidades Principais

### 11.1 CRUD de Clientes

```bash
# Listar clientes
curl -X GET https://api.seudominio.com/api/v1/clientes/ \
  -H "Authorization: Bearer {token}"
```

**Esperado**: Lista de clientes ou array vazio

### 11.2 CRUD de Documentos

```bash
# Listar documentos
curl -X GET https://api.seudominio.com/api/v1/documentos/ \
  -H "Authorization: Bearer {token}"
```

**Esperado**: Lista de documentos ou array vazio

### 11.3 Geração de Contratos

```bash
# Gerar contrato
curl -X POST https://api.seudominio.com/api/v1/documentos/gerar-contrato/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"cliente_id":1}'
```

**Esperado**: Documento gerado ou erro explicativo

---

## 🛠️ 12. Rollback (Se Necessário)

### 12.1 Verificar Tags Disponíveis

```bash
docker images | grep connect-backend
```

### 12.2 Executar Rollback

```bash
# Linux/Mac
./deploy.sh rollback v1.0.0

# Windows
.\deploy.ps1 rollback v1.0.0
```

**Verificar após rollback**:
- ✅ Containers reiniciados
- ✅ Versão anterior está rodando
- ✅ Health check funcionando

---

## 📊 13. Métricas de Estabilidade

Conforme Issue #9:

| Métrica | Objetivo | Como Medir |
|---------|----------|------------|
| **Deploy completo** | ≤ 10 minutos | Tempo desde `git pull` até serviço disponível |
| **Rollback** | ≤ 3 minutos | Tempo desde comando até serviço restaurado |
| **Uptime** | ≥ 99.5% | Monitoramento contínuo (Prometheus/UptimeRobot) |
| **Recuperação** | ≤ 2 minutos | Tempo para auto-restart após falha |

---

## 📝 14. Documentação

### 14.1 Verificar Documentos

- ✅ `README.md` está atualizado
- ✅ `docs/DEPLOY.md` existe e está completo
- ✅ `docs/ENVIRONMENT_VARIABLES.md` documenta todas as variáveis
- ✅ `docs/CORS_CONFIGURATION.md` documenta CORS

### 14.2 API Documentation

```bash
# Acessar Swagger
https://api.seudominio.com/api/docs/

# Acessar ReDoc
https://api.seudominio.com/api/redoc/

# Schema OpenAPI
https://api.seudominio.com/api/schema/
```

---

## 🔐 15. Backups

### 15.1 Backup Automático

```bash
# Verificar backups recentes
ls -lh /opt/dx-connect/backups/ | head -10
```

**Verificar**:
- ✅ Backup do banco de dados (últimas 24h)
- ✅ Backup de mídia (se configurado)
- ✅ Rotação de backups funcionando

### 15.2 Testar Restore

```bash
# Linux/Mac
./deploy.sh restore backup_20251009_200000.sql.gz

# Windows
.\deploy.ps1 restore backup_20251009_200000.sql.gz
```

---

## ✅ Checklist Final

Marque cada item após verificação:

- [ ] Todos os containers estão rodando
- [ ] Health check retorna 200 OK
- [ ] Autenticação JWT funcionando
- [ ] HTTPS configurado corretamente
- [ ] CORS configurado corretamente
- [ ] Banco de dados conectado
- [ ] Todas as migrações aplicadas
- [ ] Backup recente existe
- [ ] Tempo de resposta < 1s
- [ ] Uso de recursos OK (CPU/RAM < 80%)
- [ ] WebSocket funcionando
- [ ] Email configurado (se aplicável)
- [ ] Celery workers ativos (se aplicável)
- [ ] Monitoramento funcionando (se aplicável)
- [ ] Funcionalidades principais testadas
- [ ] Documentação atualizada
- [ ] Logs sem erros críticos
- [ ] Rollback testado (opcional, mas recomendado)

---

## 🚨 Em Caso de Problemas

### Se algo falhar:

1. **Verificar logs detalhados**:
   ```bash
   docker-compose logs --tail=100 web
   docker-compose logs --tail=100 db
   docker-compose logs --tail=100 redis
   ```

2. **Executar rollback**:
   ```bash
   ./deploy.sh rollback {versao_anterior}
   ```

3. **Reportar no Sentry** (se configurado)

4. **Documentar o incidente**

---

## 📞 Contatos de Emergência

- **DevOps Lead**: [seu-nome]
- **Tech Lead**: [nome]
- **Slack Channel**: #dx-connect-alerts
- **On-call**: [telefone/pager]

---

## 📈 Métricas Esperadas

Após deploy bem-sucedido, as métricas devem ser:

- **Response Time**: < 200ms (p95)
- **Error Rate**: < 0.1%
- **Uptime**: 100% (primeiras 24h)
- **CPU Usage**: < 50%
- **Memory Usage**: < 60%
- **Database Connections**: < 100
- **Redis Memory**: < 128MB

---

## 🎯 Próximos Passos Após Deploy

1. **Monitorar por 24h**
2. **Verificar logs diários**
3. **Coletar feedback dos usuários**
4. **Atualizar documentação se necessário**
5. **Planejar próximo deploy**

---

**✅ Deploy concluído com sucesso? Marque a issue como completa!**

