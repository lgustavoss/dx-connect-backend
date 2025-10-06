# 🚀 Deploy em Produção - DX Connect Backend

Este documento contém instruções detalhadas para fazer deploy do DX Connect Backend em ambiente de produção.

## 📋 Pré-requisitos

### Servidor
- **OS:** Ubuntu 20.04+ ou CentOS 8+ (recomendado)
- **RAM:** Mínimo 2GB, recomendado 4GB+
- **CPU:** Mínimo 2 cores, recomendado 4 cores+
- **Disco:** Mínimo 20GB de espaço livre
- **Rede:** Porta 80 e 443 abertas

### Software
- **Docker:** 20.10+
- **Docker Compose:** 2.0+
- **Git:** 2.25+
- **Certbot:** Para certificados SSL (opcional)

### Domínio e SSL
- Domínio configurado (ex: `api.seudominio.com`)
- Certificado SSL válido (recomendado: Let's Encrypt)

## 🔧 Configuração do Servidor

### 1. Instalar Docker e Docker Compose

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verificar instalação
docker --version
docker-compose --version
```

### 2. Configurar Firewall

```bash
# Ubuntu (UFW)
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable

# CentOS (firewalld)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## 📦 Deploy da Aplicação

### 1. Clone do Repositório

```bash
# Criar diretório para a aplicação
sudo mkdir -p /opt/dx-connect
sudo chown $USER:$USER /opt/dx-connect
cd /opt/dx-connect

# Clone do repositório
git clone https://github.com/seu-usuario/dx-connect-backend.git .
```

### 2. Configuração de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env.production

# Editar configurações de produção
nano .env.production
```

**Configurações importantes para produção:**

```bash
# Django
DEBUG=False
SECRET_KEY=your-very-secure-secret-key-here
ALLOWED_HOSTS=api.seudominio.com,www.seudominio.com

# Database
DB_PASSWORD=your-secure-database-password

# Email
EMAIL_HOST_PASSWORD=your-secure-email-password

# Redis
REDIS_URL=redis://redis:6379/0

# Logging
LOG_LEVEL=WARNING
```

### 3. Configurar SSL (Let's Encrypt)

```bash
# Instalar Certbot
sudo apt install certbot  # Ubuntu/Debian
# ou
sudo yum install certbot  # CentOS

# Obter certificado
sudo certbot certonly --standalone -d api.seudominio.com

# Verificar renovação automática
sudo certbot renew --dry-run
```

### 4. Configurar Nginx (Proxy Reverso)

```bash
# Instalar Nginx
sudo apt install nginx  # Ubuntu/Debian
# ou
sudo yum install nginx  # CentOS

# Criar configuração
sudo nano /etc/nginx/sites-available/dx-connect
```

**Configuração do Nginx:**

```nginx
server {
    listen 80;
    server_name api.seudominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.seudominio.com;

    ssl_certificate /etc/letsencrypt/live/api.seudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.seudominio.com/privkey.pem;

    # Configurações SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Proxy para aplicação
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Arquivos estáticos
    location /static/ {
        alias /opt/dx-connect/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Arquivos de mídia
    location /media/ {
        alias /opt/dx-connect/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
}
```

```bash
# Ativar site
sudo ln -s /etc/nginx/sites-available/dx-connect /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. Deploy da Aplicação

```bash
# Build e start dos containers
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Executar migrações
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py migrate

# Criar superusuário
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Coletar arquivos estáticos
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

## 🔄 Script de Deploy Automatizado

Crie o arquivo `deploy.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Iniciando deploy do DX Connect Backend..."

# Verificar se estamos no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Erro: docker-compose.yml não encontrado. Execute este script no diretório raiz do projeto."
    exit 1
fi

# Pull das últimas mudanças
echo "📥 Atualizando código..."
git pull origin main

# Build das imagens
echo "🔨 Buildando imagens..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Parar containers existentes
echo "🛑 Parando containers..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# Iniciar novos containers
echo "🚀 Iniciando containers..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Aguardar banco estar pronto
echo "⏳ Aguardando banco de dados..."
sleep 10

# Executar migrações
echo "🗄️ Executando migrações..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py migrate

# Coletar arquivos estáticos
echo "📁 Coletando arquivos estáticos..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Verificar saúde da aplicação
echo "🏥 Verificando saúde da aplicação..."
sleep 5
if curl -f http://localhost:8000/api/v1/health/ > /dev/null 2>&1; then
    echo "✅ Deploy concluído com sucesso!"
else
    echo "❌ Erro: Aplicação não está respondendo corretamente."
    exit 1
fi
```

```bash
# Tornar executável
chmod +x deploy.sh

# Executar deploy
./deploy.sh
```

## 📊 Monitoramento

### 1. Logs da Aplicação

```bash
# Ver logs em tempo real
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f web

# Ver logs do banco
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f db

# Ver logs do Redis
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f redis
```

### 2. Health Check

```bash
# Verificar status da aplicação
curl -s http://localhost:8000/api/v1/health/ | jq

# Verificar via Nginx
curl -s https://api.seudominio.com/api/v1/health/ | jq
```

### 3. Métricas do Sistema

```bash
# Uso de recursos
docker stats

# Espaço em disco
df -h

# Uso de memória
free -h
```

## 💾 Backup

### 1. Backup do Banco de Dados

```bash
#!/bin/bash
# backup-db.sh

BACKUP_DIR="/opt/dx-connect/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backup_${DATE}.sql"

mkdir -p $BACKUP_DIR

# Backup do PostgreSQL
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec -T db pg_dump -U dxconnect dxconnect > $BACKUP_DIR/$BACKUP_FILE

# Comprimir backup
gzip $BACKUP_DIR/$BACKUP_FILE

# Manter apenas os últimos 7 backups
cd $BACKUP_DIR
ls -t backup_*.sql.gz | tail -n +8 | xargs -r rm

echo "✅ Backup criado: $BACKUP_FILE.gz"
```

### 2. Backup dos Arquivos de Mídia

```bash
#!/bin/bash
# backup-media.sh

BACKUP_DIR="/opt/dx-connect/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="media_backup_${DATE}.tar.gz"

mkdir -p $BACKUP_DIR

# Backup dos arquivos de mídia
tar -czf $BACKUP_DIR/$BACKUP_FILE media/

echo "✅ Backup de mídia criado: $BACKUP_FILE"
```

### 3. Agendar Backups

```bash
# Editar crontab
crontab -e

# Adicionar linhas para backup diário às 2h da manhã
0 2 * * * /opt/dx-connect/backup-db.sh
0 2 * * * /opt/dx-connect/backup-media.sh
```

## 🔧 Troubleshooting

### Problemas Comuns

#### 1. Container não inicia
```bash
# Verificar logs
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs web

# Verificar configuração
docker-compose -f docker-compose.yml -f docker-compose.prod.yml config
```

#### 2. Erro de migração
```bash
# Executar migração forçada
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py migrate --fake-initial

# Resetar migrações (CUIDADO: perde dados)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py migrate --fake-initial
```

#### 3. Problemas de permissão
```bash
# Verificar ownership
ls -la /opt/dx-connect/

# Corrigir permissões
sudo chown -R $USER:$USER /opt/dx-connect/
```

#### 4. Aplicação não responde
```bash
# Verificar se containers estão rodando
docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Reiniciar containers
docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart

# Verificar logs do Nginx
sudo tail -f /var/log/nginx/error.log
```

### Comandos Úteis

```bash
# Reiniciar apenas a aplicação
docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart web

# Acessar shell do container
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web bash

# Verificar uso de recursos
docker-compose -f docker-compose.yml -f docker-compose.prod.yml top

# Limpar containers parados
docker system prune -f
```

## 🔄 Atualizações

### Atualização da Aplicação

```bash
# Fazer backup antes da atualização
./backup-db.sh
./backup-media.sh

# Executar deploy
./deploy.sh
```

### Atualização do Sistema

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
# ou
sudo yum update -y  # CentOS

# Reiniciar se necessário
sudo reboot
```

## 📞 Suporte

Em caso de problemas:

1. Verifique os logs da aplicação
2. Consulte este documento de troubleshooting
3. Verifique o status dos serviços
4. Entre em contato com a equipe de desenvolvimento

---

**Última atualização:** $(date)
**Versão da aplicação:** $(git describe --tags --always)
