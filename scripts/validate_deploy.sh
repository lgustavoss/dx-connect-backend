#!/bin/bash
# Script de Validação Pós-Deploy - DX Connect Backend
# Executa verificações automáticas após deploy

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
API_URL="${API_URL:-http://localhost:8001}"
TIMEOUT=10

# Contadores
PASSED=0
FAILED=0

# Funções auxiliares
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[✓ PASS]${NC} $1"
    ((PASSED++))
}

error() {
    echo -e "${RED}[✗ FAIL]${NC} $1"
    ((FAILED++))
}

warning() {
    echo -e "${YELLOW}[⚠ WARN]${NC} $1"
}

# Banner
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║         DX CONNECT - VALIDAÇÃO PÓS-DEPLOY                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 1. Verificar containers
log "1. Verificando containers..."
if docker-compose ps | grep -q "Up"; then
    success "Containers estão rodando"
else
    error "Alguns containers não estão rodando"
fi

# 2. Verificar health check
log "2. Verificando health check..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/api/v1/health/" --max-time $TIMEOUT)
if [ "$HTTP_CODE" = "200" ]; then
    success "Health check retornou 200 OK"
else
    error "Health check falhou (HTTP $HTTP_CODE)"
fi

# 3. Verificar banco de dados
log "3. Verificando conexão com banco de dados..."
if docker-compose exec -T db psql -U dxconnect -d dxconnect -c "SELECT 1;" > /dev/null 2>&1; then
    success "Banco de dados conectado"
else
    error "Falha na conexão com banco de dados"
fi

# 4. Verificar migrações
log "4. Verificando migrações..."
PENDING=$(docker-compose exec -T web python manage.py showmigrations --plan | grep "\[ \]" | wc -l)
if [ "$PENDING" -eq "0" ]; then
    success "Todas as migrações aplicadas"
else
    error "$PENDING migrações pendentes"
fi

# 5. Verificar Redis
log "5. Verificando Redis..."
if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
    success "Redis respondendo"
else
    error "Redis não está respondendo"
fi

# 6. Verificar DEBUG mode
log "6. Verificando modo DEBUG..."
DEBUG=$(docker-compose exec -T web env | grep "DJANGO_DEBUG" | cut -d'=' -f2)
if [ "$DEBUG" = "False" ] || [ "$DEBUG" = "false" ]; then
    success "DEBUG está desabilitado (produção)"
else
    error "DEBUG está habilitado (PERIGO EM PRODUÇÃO!)"
fi

# 7. Verificar SECRET_KEY
log "7. Verificando SECRET_KEY..."
SECRET=$(docker-compose exec -T web env | grep "DJANGO_SECRET_KEY" | cut -d'=' -f2)
if [ -n "$SECRET" ] && [ "$SECRET" != "dev-secret" ]; then
    success "SECRET_KEY configurada corretamente"
else
    error "SECRET_KEY não está configurada ou está usando valor padrão"
fi

# 8. Verificar ALLOWED_HOSTS
log "8. Verificando ALLOWED_HOSTS..."
HOSTS=$(docker-compose exec -T web env | grep "DJANGO_ALLOWED_HOSTS")
if [ -n "$HOSTS" ]; then
    success "ALLOWED_HOSTS configurado"
else
    warning "ALLOWED_HOSTS pode não estar configurado"
fi

# 9. Verificar logs recentes
log "9. Verificando logs por erros..."
ERRORS=$(docker-compose logs --tail=100 web 2>&1 | grep -i "error\|critical\|exception" | wc -l)
if [ "$ERRORS" -lt "5" ]; then
    success "Poucos erros nos logs ($ERRORS encontrados)"
else
    warning "Muitos erros nos logs ($ERRORS encontrados) - verificar manualmente"
fi

# 10. Verificar backups
log "10. Verificando backups..."
if [ -d "/opt/dx-connect/backups" ]; then
    RECENT_BACKUP=$(find /opt/dx-connect/backups -name "*.sql.gz" -mtime -1 | wc -l)
    if [ "$RECENT_BACKUP" -gt "0" ]; then
        success "Backup recente encontrado"
    else
        warning "Nenhum backup nas últimas 24h"
    fi
else
    warning "Diretório de backups não encontrado"
fi

# Resumo
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Testes passados: $PASSED${NC}"
echo -e "${RED}Testes falhados: $FAILED${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ Deploy validado com sucesso!${NC}"
    exit 0
else
    echo -e "${RED}✗ Deploy tem $FAILED problema(s) - verifique os logs acima${NC}"
    exit 1
fi

