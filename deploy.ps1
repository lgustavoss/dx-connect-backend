# Script de Deploy para Produção - DX Connect Backend (PowerShell)
# Uso: .\deploy.ps1 [opção]
# Opções: build, start, stop, restart, logs, backup, restore

param(
    [string]$Action = "deploy"
)

# Configurações
$ProjectName = "dx-connect-backend"
$ComposeFiles = "-f docker-compose.yml -f docker-compose.prod.yml"
$BackupDir = ".\backups"
$LogFile = ".\deploy.log"

# Função para logging
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] [$Level] $Message"
    Write-Host $LogMessage
    Add-Content -Path $LogFile -Value $LogMessage
}

function Write-Error-Log {
    param([string]$Message)
    Write-Log $Message "ERROR"
    exit 1
}

function Write-Success-Log {
    param([string]$Message)
    Write-Log $Message "SUCCESS"
}

function Write-Warning-Log {
    param([string]$Message)
    Write-Log $Message "WARNING"
}

# Verificar se estamos no diretório correto
function Test-Directory {
    if (-not (Test-Path "docker-compose.yml")) {
        Write-Error-Log "docker-compose.yml não encontrado. Execute este script no diretório raiz do projeto."
    }
    
    if (-not (Test-Path "docker-compose.prod.yml")) {
        Write-Error-Log "docker-compose.prod.yml não encontrado."
    }
    
    if (-not (Test-Path ".env.production")) {
        Write-Warning-Log ".env.production não encontrado. Usando .env.example como base."
        Copy-Item ".env.example" ".env.production"
        Write-Warning-Log "Configure o arquivo .env.production antes de continuar."
        exit 1
    }
}

# Verificar dependências
function Test-Dependencies {
    Write-Log "Verificando dependências..."
    
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error-Log "Docker não está instalado."
    }
    
    if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
        Write-Error-Log "Docker Compose não está instalado."
    }
    
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Error-Log "Git não está instalado."
    }
    
    Write-Success-Log "Todas as dependências estão instaladas."
}

# Backup do banco de dados
function Backup-Database {
    Write-Log "Criando backup do banco de dados..."
    
    if (-not (Test-Path $BackupDir)) {
        New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    }
    
    $Date = Get-Date -Format "yyyyMMdd_HHmmss"
    $BackupFile = "backup_$Date.sql"
    
    try {
        docker-compose $ComposeFiles exec -T db pg_dump -U dxconnect dxconnect | Out-File -FilePath "$BackupDir\$BackupFile" -Encoding UTF8
        Compress-Archive -Path "$BackupDir\$BackupFile" -DestinationPath "$BackupDir\$BackupFile.zip" -Force
        Remove-Item "$BackupDir\$BackupFile"
        Write-Success-Log "Backup criado: $BackupFile.zip"
        
        # Manter apenas os últimos 7 backups
        Get-ChildItem "$BackupDir\backup_*.sql.zip" | Sort-Object LastWriteTime -Descending | Select-Object -Skip 7 | Remove-Item -Force
    }
    catch {
        Write-Warning-Log "Não foi possível criar backup do banco de dados: $($_.Exception.Message)"
    }
}

# Backup dos arquivos de mídia
function Backup-Media {
    Write-Log "Criando backup dos arquivos de mídia..."
    
    if (-not (Test-Path $BackupDir)) {
        New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    }
    
    $Date = Get-Date -Format "yyyyMMdd_HHmmss"
    $BackupFile = "media_backup_$Date.zip"
    
    if (Test-Path "media") {
        Compress-Archive -Path "media" -DestinationPath "$BackupDir\$BackupFile" -Force
        Write-Success-Log "Backup de mídia criado: $BackupFile"
    }
    else {
        Write-Warning-Log "Diretório media não encontrado."
    }
}

# Build das imagens
function Build-Images {
    Write-Log "Buildando imagens Docker..."
    
    try {
        docker-compose $ComposeFiles build --no-cache
        Write-Success-Log "Imagens buildadas com sucesso."
    }
    catch {
        Write-Error-Log "Falha ao buildar imagens: $($_.Exception.Message)"
    }
}

# Iniciar containers
function Start-Containers {
    Write-Log "Iniciando containers..."
    
    try {
        docker-compose $ComposeFiles up -d
        Write-Success-Log "Containers iniciados com sucesso."
    }
    catch {
        Write-Error-Log "Falha ao iniciar containers: $($_.Exception.Message)"
    }
}

# Parar containers
function Stop-Containers {
    Write-Log "Parando containers..."
    
    try {
        docker-compose $ComposeFiles down
        Write-Success-Log "Containers parados com sucesso."
    }
    catch {
        Write-Error-Log "Falha ao parar containers: $($_.Exception.Message)"
    }
}

# Reiniciar containers
function Restart-Containers {
    Write-Log "Reiniciando containers..."
    
    try {
        docker-compose $ComposeFiles restart
        Write-Success-Log "Containers reiniciados com sucesso."
    }
    catch {
        Write-Error-Log "Falha ao reiniciar containers: $($_.Exception.Message)"
    }
}

# Executar migrações
function Invoke-Migrations {
    Write-Log "Executando migrações do banco de dados..."
    
    # Aguardar banco estar pronto
    Write-Log "Aguardando banco de dados estar pronto..."
    Start-Sleep -Seconds 10
    
    try {
        docker-compose $ComposeFiles exec web python manage.py migrate
        Write-Success-Log "Migrações executadas com sucesso."
    }
    catch {
        Write-Error-Log "Falha ao executar migrações: $($_.Exception.Message)"
    }
}

# Coletar arquivos estáticos
function Collect-Static {
    Write-Log "Coletando arquivos estáticos..."
    
    try {
        docker-compose $ComposeFiles exec web python manage.py collectstatic --noinput
        Write-Success-Log "Arquivos estáticos coletados com sucesso."
    }
    catch {
        Write-Error-Log "Falha ao coletar arquivos estáticos: $($_.Exception.Message)"
    }
}

# Verificar saúde da aplicação
function Test-Health {
    Write-Log "Verificando saúde da aplicação..."
    
    # Aguardar aplicação estar pronta
    Start-Sleep -Seconds 15
    
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health/" -Method GET -TimeoutSec 10
        if ($Response.StatusCode -eq 200) {
            Write-Success-Log "Aplicação está respondendo corretamente."
        }
        else {
            Write-Error-Log "Aplicação não está respondendo corretamente. Status: $($Response.StatusCode)"
        }
    }
    catch {
        Write-Error-Log "Aplicação não está respondendo. Verifique os logs: $($_.Exception.Message)"
    }
}

# Mostrar logs
function Show-Logs {
    Write-Log "Mostrando logs da aplicação..."
    docker-compose $ComposeFiles logs -f web
}

# Deploy completo
function Start-FullDeploy {
    Write-Log "Iniciando deploy completo do $ProjectName..."
    
    Test-Directory
    Test-Dependencies
    
    # Fazer backup antes do deploy
    Backup-Database
    Backup-Media
    
    # Pull das últimas mudanças
    Write-Log "Atualizando código do repositório..."
    try {
        git pull origin main
        Write-Success-Log "Código atualizado com sucesso."
    }
    catch {
        Write-Warning-Log "Falha ao atualizar código. Continuando com versão atual: $($_.Exception.Message)"
    }
    
    # Build das imagens
    Build-Images
    
    # Parar containers existentes
    Stop-Containers
    
    # Iniciar novos containers
    Start-Containers
    
    # Executar migrações
    Invoke-Migrations
    
    # Coletar arquivos estáticos
    Collect-Static
    
    # Verificar saúde da aplicação
    Test-Health
    
    Write-Success-Log "Deploy completo finalizado com sucesso!"
}

# Criar superusuário
function New-SuperUser {
    Write-Log "Criando superusuário..."
    
    try {
        docker-compose $ComposeFiles exec web python manage.py createsuperuser
        Write-Success-Log "Superusuário criado com sucesso."
    }
    catch {
        Write-Error-Log "Falha ao criar superusuário: $($_.Exception.Message)"
    }
}

# Mostrar status dos containers
function Show-Status {
    Write-Log "Status dos containers:"
    docker-compose $ComposeFiles ps
}

# Mostrar uso de recursos
function Show-Stats {
    Write-Log "Uso de recursos:"
    docker stats --no-stream
}

# Limpeza do sistema
function Clear-System {
    Write-Log "Limpando sistema Docker..."
    
    # Remover containers parados
    docker container prune -f
    
    # Remover imagens não utilizadas
    docker image prune -f
    
    # Remover volumes não utilizados
    docker volume prune -f
    
    Write-Success-Log "Limpeza concluída."
}

# Mostrar ajuda
function Show-Help {
    Write-Host "Script de Deploy para Produção - DX Connect Backend (PowerShell)"
    Write-Host ""
    Write-Host "Uso: .\deploy.ps1 [opção]"
    Write-Host ""
    Write-Host "Opções:"
    Write-Host "  build         - Buildar imagens Docker"
    Write-Host "  start         - Iniciar containers"
    Write-Host "  stop          - Parar containers"
    Write-Host "  restart       - Reiniciar containers"
    Write-Host "  deploy        - Deploy completo (padrão)"
    Write-Host "  logs          - Mostrar logs da aplicação"
    Write-Host "  status        - Mostrar status dos containers"
    Write-Host "  stats         - Mostrar uso de recursos"
    Write-Host "  backup        - Fazer backup do banco e mídia"
    Write-Host "  superuser     - Criar superusuário"
    Write-Host "  cleanup       - Limpar sistema Docker"
    Write-Host "  help          - Mostrar esta ajuda"
    Write-Host ""
}

# Main
switch ($Action.ToLower()) {
    "build" {
        Test-Directory
        Test-Dependencies
        Build-Images
    }
    "start" {
        Test-Directory
        Start-Containers
    }
    "stop" {
        Test-Directory
        Stop-Containers
    }
    "restart" {
        Test-Directory
        Restart-Containers
    }
    "deploy" {
        Start-FullDeploy
    }
    "logs" {
        Test-Directory
        Show-Logs
    }
    "status" {
        Test-Directory
        Show-Status
    }
    "stats" {
        Show-Stats
    }
    "backup" {
        Test-Directory
        Backup-Database
        Backup-Media
    }
    "superuser" {
        Test-Directory
        New-SuperUser
    }
    "cleanup" {
        Clear-System
    }
    "help" {
        Show-Help
    }
    default {
        Write-Error-Log "Opção inválida: $Action. Use '.\deploy.ps1 help' para ver as opções disponíveis."
    }
}
