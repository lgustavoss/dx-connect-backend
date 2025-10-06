#!/bin/bash
# Script de Deploy para Produção - DX Connect Backend
# Uso: ./deploy.sh [opção]
# Opções: build, start, stop, restart, logs, backup, restore

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
PROJECT_NAME="dx-connect-backend"
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
BACKUP_DIR="/opt/dx-connect/backups"
LOG_FILE="/var/log/dx-connect-deploy.log"

# Função para logging
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a $LOG_FILE
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a $LOG_FILE
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a $LOG_FILE
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a $LOG_FILE
}

# Verificar se estamos no diretório correto
check_directory() {
    if [ ! -f "docker-compose.yml" ]; then
        error "docker-compose.yml não encontrado. Execute este script no diretório raiz do projeto."
    fi
    
    if [ ! -f "docker-compose.prod.yml" ]; then
        error "docker-compose.prod.yml não encontrado."
    fi
    
    if [ ! -f ".env.production" ]; then
        warning ".env.production não encontrado. Usando .env.example como base."
        cp .env.example .env.production
        warning "Configure o arquivo .env.production antes de continuar."
        exit 1
    fi
}

# Verificar dependências
check_dependencies() {
    log "Verificando dependências..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker não está instalado."
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose não está instalado."
    fi
    
    if ! command -v git &> /dev/null; then
        error "Git não está instalado."
    fi
    
    success "Todas as dependências estão instaladas."
}

# Backup do banco de dados
backup_database() {
    log "Criando backup do banco de dados..."
    
    mkdir -p $BACKUP_DIR
    DATE=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="backup_${DATE}.sql"
    
    if docker-compose $COMPOSE_FILES exec -T db pg_dump -U dxconnect dxconnect > $BACKUP_DIR/$BACKUP_FILE 2>/dev/null; then
        gzip $BACKUP_DIR/$BACKUP_FILE
        success "Backup criado: $BACKUP_FILE.gz"
        
        # Manter apenas os últimos 7 backups
        cd $BACKUP_DIR
        ls -t backup_*.sql.gz | tail -n +8 | xargs -r rm -f
        cd - > /dev/null
    else
        warning "Não foi possível criar backup do banco de dados."
    fi
}

# Backup dos arquivos de mídia
backup_media() {
    log "Criando backup dos arquivos de mídia..."
    
    mkdir -p $BACKUP_DIR
    DATE=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="media_backup_${DATE}.tar.gz"
    
    if [ -d "media" ]; then
        tar -czf $BACKUP_DIR/$BACKUP_FILE media/
        success "Backup de mídia criado: $BACKUP_FILE"
    else
        warning "Diretório media não encontrado."
    fi
}

# Build das imagens
build_images() {
    log "Buildando imagens Docker..."
    
    if docker-compose $COMPOSE_FILES build --no-cache; then
        success "Imagens buildadas com sucesso."
    else
        error "Falha ao buildar imagens."
    fi
}

# Iniciar containers
start_containers() {
    log "Iniciando containers..."
    
    if docker-compose $COMPOSE_FILES up -d; then
        success "Containers iniciados com sucesso."
    else
        error "Falha ao iniciar containers."
    fi
}

# Parar containers
stop_containers() {
    log "Parando containers..."
    
    if docker-compose $COMPOSE_FILES down; then
        success "Containers parados com sucesso."
    else
        error "Falha ao parar containers."
    fi
}

# Reiniciar containers
restart_containers() {
    log "Reiniciando containers..."
    
    if docker-compose $COMPOSE_FILES restart; then
        success "Containers reiniciados com sucesso."
    else
        error "Falha ao reiniciar containers."
    fi
}

# Executar migrações
run_migrations() {
    log "Executando migrações do banco de dados..."
    
    # Aguardar banco estar pronto
    log "Aguardando banco de dados estar pronto..."
    sleep 10
    
    if docker-compose $COMPOSE_FILES exec web python manage.py migrate; then
        success "Migrações executadas com sucesso."
    else
        error "Falha ao executar migrações."
    fi
}

# Coletar arquivos estáticos
collect_static() {
    log "Coletando arquivos estáticos..."
    
    if docker-compose $COMPOSE_FILES exec web python manage.py collectstatic --noinput; then
        success "Arquivos estáticos coletados com sucesso."
    else
        error "Falha ao coletar arquivos estáticos."
    fi
}

# Verificar saúde da aplicação
health_check() {
    log "Verificando saúde da aplicação..."
    
    # Aguardar aplicação estar pronta
    sleep 15
    
    if curl -f http://localhost:8000/api/v1/health/ > /dev/null 2>&1; then
        success "Aplicação está respondendo corretamente."
    else
        error "Aplicação não está respondendo. Verifique os logs."
    fi
}

# Mostrar logs
show_logs() {
    log "Mostrando logs da aplicação..."
    docker-compose $COMPOSE_FILES logs -f web
}

# Deploy completo
full_deploy() {
    log "Iniciando deploy completo do $PROJECT_NAME..."
    
    check_directory
    check_dependencies
    
    # Fazer backup antes do deploy
    backup_database
    backup_media
    
    # Pull das últimas mudanças
    log "Atualizando código do repositório..."
    if git pull origin main; then
        success "Código atualizado com sucesso."
    else
        warning "Falha ao atualizar código. Continuando com versão atual."
    fi
    
    # Build das imagens
    build_images
    
    # Parar containers existentes
    stop_containers
    
    # Iniciar novos containers
    start_containers
    
    # Executar migrações
    run_migrations
    
    # Coletar arquivos estáticos
    collect_static
    
    # Verificar saúde da aplicação
    health_check
    
    success "Deploy completo finalizado com sucesso!"
}

# Criar superusuário
create_superuser() {
    log "Criando superusuário..."
    
    if docker-compose $COMPOSE_FILES exec web python manage.py createsuperuser; then
        success "Superusuário criado com sucesso."
    else
        error "Falha ao criar superusuário."
    fi
}

# Mostrar status dos containers
show_status() {
    log "Status dos containers:"
    docker-compose $COMPOSE_FILES ps
}

# Mostrar uso de recursos
show_stats() {
    log "Uso de recursos:"
    docker stats --no-stream
}

# Limpeza do sistema
cleanup() {
    log "Limpando sistema Docker..."
    
    # Remover containers parados
    docker container prune -f
    
    # Remover imagens não utilizadas
    docker image prune -f
    
    # Remover volumes não utilizados
    docker volume prune -f
    
    success "Limpeza concluída."
}

# Mostrar ajuda
show_help() {
    echo "Script de Deploy para Produção - DX Connect Backend"
    echo ""
    echo "Uso: $0 [opção]"
    echo ""
    echo "Opções:"
    echo "  build         - Buildar imagens Docker"
    echo "  start         - Iniciar containers"
    echo "  stop          - Parar containers"
    echo "  restart       - Reiniciar containers"
    echo "  deploy        - Deploy completo (padrão)"
    echo "  logs          - Mostrar logs da aplicação"
    echo "  status        - Mostrar status dos containers"
    echo "  stats         - Mostrar uso de recursos"
    echo "  backup        - Fazer backup do banco e mídia"
    echo "  superuser     - Criar superusuário"
    echo "  cleanup       - Limpar sistema Docker"
    echo "  help          - Mostrar esta ajuda"
    echo ""
}

# Main
main() {
    case "${1:-deploy}" in
        "build")
            check_directory
            check_dependencies
            build_images
            ;;
        "start")
            check_directory
            start_containers
            ;;
        "stop")
            check_directory
            stop_containers
            ;;
        "restart")
            check_directory
            restart_containers
            ;;
        "deploy")
            full_deploy
            ;;
        "logs")
            check_directory
            show_logs
            ;;
        "status")
            check_directory
            show_status
            ;;
        "stats")
            show_stats
            ;;
        "backup")
            check_directory
            backup_database
            backup_media
            ;;
        "superuser")
            check_directory
            create_superuser
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            error "Opção inválida: $1. Use '$0 help' para ver as opções disponíveis."
            ;;
    esac
}

# Executar função principal
main "$@"
