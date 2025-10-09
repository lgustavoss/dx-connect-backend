# 🚀 Guia Rápido de Deploy - DX Connect Backend

## ⚡ Deploy Rápido (Desenvolvimento)

```bash
# 1. Clone o repositório
git clone https://github.com/lgustavoss/dx-connect-backend.git
cd dx-connect-backend

# 2. Inicie os containers
docker-compose up -d

# 3. Aguarde ~30 segundos e acesse
http://localhost:8001/api/v1/health/
```

**Pronto! 🎉** O backend está rodando em modo desenvolvimento.

---

## 🏭 Deploy em Produção (10 Minutos)

### Passo 1: Preparar Servidor (5min)

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Relogar para aplicar grupo docker
exit
# (faça login novamente)
```

### Passo 2: Clonar e Configurar (3min)

```bash
# Clone o repositório
git clone https://github.com/lgustavoss/dx-connect-backend.git
cd dx-connect-backend

# Criar arquivo de ambiente
cp .env.example .env.production

# Editar configurações (IMPORTANTE!)
nano .env.production
```

**Configurações mínimas obrigatórias**:
```env
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=sua-chave-secreta-aqui-minimo-50-caracteres
DJANGO_ALLOWED_HOSTS=api.seudominio.com,seudominio.com
CORS_ALLOWED_ORIGINS=https://app.seudominio.com
POSTGRES_PASSWORD=senha-forte-do-banco
```

### Passo 3: Deploy (2min)

```bash
# Build e start
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Aguardar inicialização (~30 segundos)
sleep 30

# Validar deploy
bash scripts/validate_deploy.sh
```

---

## 🔄 Atualizações (5 Minutos)

```bash
# 1. Fazer backup
bash deploy.sh backup

# 2. Atualizar código
git pull origin main

# 3. Rebuild e restart
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# 4. Validar
bash scripts/validate_deploy.sh
```

---

## ⏪ Rollback (3 Minutos)

```bash
# 1. Listar versões disponíveis
docker images | grep connect-backend

# 2. Executar rollback
bash deploy.sh rollback v1.0.0

# 3. Validar
bash scripts/validate_deploy.sh
```

---

## 🔍 Verificação Rápida

### Status dos Containers
```bash
docker-compose ps
```

### Logs em Tempo Real
```bash
docker-compose logs -f web
```

### Health Check
```bash
curl https://api.seudominio.com/api/v1/health/
```

### Teste de Autenticação
```bash
curl -X POST https://api.seudominio.com/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"sua-senha"}'
```

---

## 🆘 Problemas Comuns

### Container não inicia
```bash
# Ver logs
docker-compose logs web --tail=50

# Restart
docker-compose restart web
```

### Erro de migração
```bash
# Aplicar migrações manualmente
docker-compose exec web python manage.py migrate
```

### Erro de permissão
```bash
# Ajustar permissões
sudo chown -R $USER:$USER .
```

### Erro de conexão com banco
```bash
# Verificar se o banco está rodando
docker-compose ps db

# Restart do banco
docker-compose restart db
```

---

## 📞 Suporte

- **Documentação Completa**: `docs/DEPLOY.md`
- **Checklist Pós-Deploy**: `docs/POST_DEPLOY_CHECKLIST.md`
- **Variáveis de Ambiente**: `docs/ENVIRONMENT_VARIABLES.md`
- **Configuração CORS**: `docs/CORS_CONFIGURATION.md`

---

## 🎯 Checklist Mínimo

Após deploy, verifique:

- [ ] Health check retorna 200
- [ ] DEBUG=False em produção
- [ ] SECRET_KEY configurada
- [ ] HTTPS funcionando
- [ ] Backup criado
- [ ] Logs sem erros críticos

---

**✅ Deploy bem-sucedido? Próximo passo: Monitoramento contínuo!**

