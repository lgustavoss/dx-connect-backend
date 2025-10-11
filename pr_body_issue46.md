# PR: WhatsApp - Processamento de Mídias (Issue #46)

## 📋 Descrição

Implementação completa de sistema de processamento de mídias WhatsApp com download, conversão, thumbnails, armazenamento seguro e limpeza automática.

Fecha #46

---

## ✨ Funcionalidades Implementadas

### 1. **Modelo MediaFile**
- ✅ Armazenamento de metadados completos
- ✅ Suporte para image, audio, video, document, sticker
- ✅ Hash SHA-256 para deduplicação
- ✅ Métricas de tempo (download + processamento)
- ✅ Controle de acesso e contador de visualizações

### 2. **Serviço de Processamento (`MediaProcessingService`)**
- ✅ Download de mídia com timeout e limite de tamanho (50MB)
- ✅ Geração automática de thumbnails (imagens)
- ✅ Conversão para formatos web-optimized (JPEG 85% quality)
- ✅ Cálculo de dimensões (width x height)
- ✅ Tratamento de erros robusto

### 3. **Tasks Celery**
- ✅ `process_media_task`: Processamento assíncrono com 2 retentativas
- ✅ `cleanup_orphan_media_files`: Limpeza automática periódica
  - Remove mídias com erro após 3 dias
  - Remove mídias não acessadas há 90+ dias
  - Calcula espaço liberado

### 4. **URLs Assinadas**
- ✅ `generate_signed_url()`: URLs temporárias com token
- ✅ Expiração configurável (padrão: 1 hora)
- ✅ Segurança via `TimestampSigner`

### 5. **Pipeline Completo**
```
Mensagem recebida com mídia
    ↓
Download da mídia (MediaProcessingService)
    ↓
Cálculo de hash SHA-256
    ↓
Salvar arquivo original
    ↓
[Se imagem] Gerar thumbnail (300x300)
    ↓
[Se imagem] Converter para JPEG otimizado
    ↓
Salvar metadados no banco
    ↓
Mídia pronta para servir
```

---

## 📂 Arquivos Criados

### Modelos e Serviços
```
whatsapp/
├── media.py              # Modelo MediaFile
├── media_service.py      # MediaProcessingService
└── tasks.py             # Tasks Celery (atualizado)
```

---

## 📊 Modelo MediaFile

### Campos Principais
| Campo | Tipo | Descrição |
|-------|------|-----------|
| file_id | UUID | ID único do arquivo |
| message | FK | Mensagem WhatsApp associada |
| original_url | URL | URL original no WhatsApp |
| media_type | CharField | image/audio/video/document |
| mime_type | CharField | Tipo MIME completo |
| file_size | BigInt | Tamanho em bytes |
| file_hash | CharField | SHA-256 para deduplicação |
| original_file | FileField | Arquivo original |
| converted_file | FileField | Versão otimizada |
| thumbnail_file | ImageField | Miniatura |
| status | CharField | pending/downloading/processing/ready/error |
| download_time_ms | Integer | Tempo de download |
| processing_time_ms | Integer | Tempo de processamento |
| access_count | Integer | Contador de acessos |

### Propriedades
- `total_processing_time_ms`: Tempo total (download + processamento)
- `file_size_mb`: Tamanho em MB
- `has_thumbnail`: Verifica se tem thumbnail
- `has_converted`: Verifica se tem versão convertida

### Métodos
- `get_primary_file()`: Retorna arquivo principal (convertido ou original)
- `increment_access()`: Incrementa contador de acesso
- `generate_signed_url(expiration_seconds)`: Gera URL assinada

---

## 🔧 MediaProcessingService

### Métodos Principais

#### download_media(url, message)
```python
media_file = MediaProcessingService.download_media(
    url="https://whatsapp.com/media/abc123",
    message=whatsapp_message
)
```
- Baixa mídia com timeout de 30s
- Valida tamanho máximo (50MB)
- Calcula hash SHA-256
- Salva arquivo original
- Retorna `MediaFile` ou `None`

#### process_media(media_file)
```python
success = MediaProcessingService.process_media(media_file)
```
- Gera thumbnail (300x300)
- Converte para JPEG (85% quality)
- Extrai dimensões
- Atualiza status

---

## 🔄 Tasks Celery

### process_media_task
```python
from whatsapp.tasks import process_media_task

# Enfileira processamento
process_media_task.delay(media_file_id=123)
```

**Configuração:**
- Max retries: 2
- Delay: 120 segundos
- Autoretry em caso de falha

### cleanup_orphan_media_files
```python
# Executar manualmente
from whatsapp.tasks import cleanup_orphan_media_files
cleanup_orphan_media_files.delay()
```

**Remove:**
- Mídias com erro após 3 dias
- Mídias não acessadas há 90+ dias

**Retorna:**
```json
{
  "deleted_count": 15,
  "freed_space_mb": 245.67
}
```

---

## 🔒 URLs Assinadas

### Gerar URL Segura
```python
media_file = MediaFile.objects.get(file_id=uuid)

# URL válida por 1 hora
url = media_file.generate_signed_url(expiration_seconds=3600)

# URL: /media/whatsapp/media/secure/{uuid}/?token=abc123:timestamp:signature
```

### Validar Token
```python
from django.core.signing import TimestampSigner

signer = TimestampSigner()
try:
    original_value = signer.unsign(token, max_age=3600)
    # Token válido
except SignatureExpired:
    # Token expirado
except BadSignature:
    # Token inválido
```

---

## 📈 Métricas e Logs

### Logs de Download
```
INFO: Baixando mídia: https://whatsapp.com/media/abc123
INFO: Mídia baixada com sucesso: uuid-123 (2.5 MB, 1230ms)
```

### Logs de Processamento
```
INFO: Processando mídia: uuid-123
DEBUG: Thumbnail gerado: uuid-123_thumb.jpg
DEBUG: Imagem convertida para JPEG: uuid-123_optimized.jpg
INFO: Mídia processada com sucesso: uuid-123 (450ms)
```

### Logs de Limpeza
```
INFO: [Task] Iniciando limpeza de mídias órfãs
INFO: [Task] Limpeza concluída: 15 mídias removidas, 245.67 MB liberados
```

---

## 🎯 Critérios de Aceitação (Issue #46)

- [x] ✅ Download da mídia do WhatsApp → Servidor
- [x] ✅ Conversão para formatos web-optimized
- [x] ✅ Geração de thumbnails (imagens)
- [x] ✅ URLs seguras (assinadas)
- [x] ✅ Metadados (tipo, tamanho, dimensões)
- [x] ✅ Limpeza de arquivos órfãos
- [x] ✅ Observabilidade (logs e métricas)
- [ ] ⏳ Endpoints para servir mídia (simplificado)

---

## 📝 Checklist

- [x] Modelo MediaFile criado
- [x] MediaProcessingService implementado
- [x] Download de mídia
- [x] Geração de thumbnails
- [x] Conversão para formatos otimizados
- [x] Hash SHA-256 para deduplicação
- [x] Tasks Celery criadas
- [x] Limpeza automática
- [x] URLs assinadas
- [x] Logs estruturados
- [x] Métricas de tempo
- [x] Documentação criada
- [ ] Endpoints de API (próximo passo)
- [ ] Testes unitários (próximo passo)

---

## 🚀 Deploy

### 1. Aplicar Migrations
```bash
docker-compose exec web python manage.py makemigrations whatsapp
docker-compose exec web python manage.py migrate
```

### 2. Configurar Celery Beat
Adicionar ao `config/celery.py`:
```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'cleanup-orphan-media': {
        'task': 'whatsapp.tasks.cleanup_orphan_media_files',
        'schedule': crontab(hour=2, minute=0),  # Diariamente às 2h
    },
}
```

### 3. Reiniciar Workers
```bash
docker-compose restart worker beat
```

---

## ⚠️ Limitações e Próximos Passos

### Implementado Neste PR
✅ Modelo completo
✅ Serviço de processamento
✅ Download e conversão
✅ Thumbnails para imagens
✅ Tasks Celery
✅ URLs assinadas
✅ Limpeza automática

### Para Próximo PR
⏳ View para servir mídia com autenticação
⏳ Suporte a S3/storage externo
⏳ Thumbnails de vídeo (requer ffmpeg)
⏳ Testes unitários completos

---

## 🔗 Referências

- **Issue**: #46 - WhatsApp: Processamento de Mídias
- **Sprint**: 3 - Atendimento via Chat
- **Issues Anteriores**: #36, #44, #45

---

## 🎉 Impacto

### Funcionalidades
- ✅ Sistema completo de processamento de mídias
- ✅ Otimização automática para web
- ✅ Thumbnails para pré-visualização rápida
- ✅ Controle de espaço em disco
- ✅ Segurança com URLs assinadas

### Performance
- Download com timeout (30s)
- Conversão otimizada (JPEG 85%)
- Thumbnails pequenos (300x300)
- Processamento assíncrono (não bloqueia API)

### Manutenção
- Limpeza automática de arquivos antigos
- Métricas detalhadas de tempo
- Logs estruturados
- Deduplicação por hash

---

**Desenvolvido com ❤️ para o DX Connect**

