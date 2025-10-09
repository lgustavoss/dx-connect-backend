# Script de Validação Pós-Deploy - DX Connect Backend (Windows)
# Executa verificações automáticas após deploy

param(
    [string]$ApiUrl = "http://localhost:8001"
)

$ErrorActionPreference = "Continue"

# Contadores
$script:Passed = 0
$script:Failed = 0

# Funções auxiliares
function Write-Log {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[✓ PASS] $Message" -ForegroundColor Green
    $script:Passed++
}

function Write-Failure {
    param([string]$Message)
    Write-Host "[✗ FAIL] $Message" -ForegroundColor Red
    $script:Failed++
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[⚠ WARN] $Message" -ForegroundColor Yellow
}

# Banner
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║         DX CONNECT - VALIDAÇÃO PÓS-DEPLOY                 ║" -ForegroundColor Blue
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Blue
Write-Host ""

# 1. Verificar containers
Write-Log "1. Verificando containers..."
$containers = docker-compose ps
if ($containers -match "Up") {
    Write-Success "Containers estão rodando"
} else {
    Write-Failure "Alguns containers não estão rodando"
}

# 2. Verificar health check
Write-Log "2. Verificando health check..."
try {
    $response = Invoke-WebRequest -Uri "$ApiUrl/api/v1/health/" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Success "Health check retornou 200 OK"
    } else {
        Write-Failure "Health check falhou (HTTP $($response.StatusCode))"
    }
} catch {
    Write-Failure "Health check não acessível"
}

# 3. Verificar banco de dados
Write-Log "3. Verificando conexão com banco de dados..."
try {
    $dbTest = docker-compose exec -T db psql -U dxconnect -d dxconnect -c "SELECT 1;" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Banco de dados conectado"
    } else {
        Write-Failure "Falha na conexão com banco de dados"
    }
} catch {
    Write-Failure "Erro ao verificar banco de dados"
}

# 4. Verificar migrações
Write-Log "4. Verificando migrações..."
try {
    $migrations = docker-compose exec -T web python manage.py showmigrations --plan 2>$null
    $pending = ($migrations | Select-String "\[ \]").Count
    if ($pending -eq 0) {
        Write-Success "Todas as migrações aplicadas"
    } else {
        Write-Failure "$pending migrações pendentes"
    }
} catch {
    Write-Warning "Não foi possível verificar migrações"
}

# 5. Verificar Redis
Write-Log "5. Verificando Redis..."
try {
    $redis = docker-compose exec -T redis redis-cli ping 2>$null
    if ($redis -match "PONG") {
        Write-Success "Redis respondendo"
    } else {
        Write-Failure "Redis não está respondendo"
    }
} catch {
    Write-Failure "Erro ao verificar Redis"
}

# 6. Verificar DEBUG mode
Write-Log "6. Verificando modo DEBUG..."
try {
    $env = docker-compose exec -T web env 2>$null
    $debug = ($env | Select-String "DJANGO_DEBUG").ToString().Split('=')[1]
    if ($debug -eq "False" -or $debug -eq "false") {
        Write-Success "DEBUG está desabilitado (produção)"
    } else {
        Write-Failure "DEBUG está habilitado (PERIGO EM PRODUÇÃO!)"
    }
} catch {
    Write-Warning "Não foi possível verificar DEBUG mode"
}

# 7. Verificar SECRET_KEY
Write-Log "7. Verificando SECRET_KEY..."
try {
    $env = docker-compose exec -T web env 2>$null
    $secret = ($env | Select-String "DJANGO_SECRET_KEY").ToString().Split('=')[1]
    if ($secret -and $secret -ne "dev-secret") {
        Write-Success "SECRET_KEY configurada corretamente"
    } else {
        Write-Failure "SECRET_KEY não está configurada ou está usando valor padrão"
    }
} catch {
    Write-Warning "Não foi possível verificar SECRET_KEY"
}

# 8. Verificar logs por erros
Write-Log "8. Verificando logs por erros..."
try {
    $logs = docker-compose logs --tail=100 web 2>&1
    $errors = ($logs | Select-String -Pattern "ERROR|CRITICAL|Exception").Count
    if ($errors -lt 5) {
        Write-Success "Poucos erros nos logs ($errors encontrados)"
    } else {
        Write-Warning "Muitos erros nos logs ($errors encontrados) - verificar manualmente"
    }
} catch {
    Write-Warning "Não foi possível verificar logs"
}

# 9. Verificar uso de recursos
Write-Log "9. Verificando uso de recursos..."
try {
    $stats = docker stats --no-stream --format "{{.Container}}: CPU={{.CPUPerc}} MEM={{.MemPerc}}"
    Write-Host $stats
    Write-Success "Uso de recursos coletado"
} catch {
    Write-Warning "Não foi possível verificar uso de recursos"
}

# Resumo
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Blue
Write-Host "Testes passados: $script:Passed" -ForegroundColor Green
Write-Host "Testes falhados: $script:Failed" -ForegroundColor Red
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Blue

if ($script:Failed -eq 0) {
    Write-Host "✓ Deploy validado com sucesso!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ Deploy tem $script:Failed problema(s) - verifique os logs acima" -ForegroundColor Red
    exit 1
}

