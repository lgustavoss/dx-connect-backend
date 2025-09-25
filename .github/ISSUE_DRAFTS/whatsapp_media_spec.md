# WhatsApp: Processamento de Mídias – Especificação

Pipeline:
- Download da mídia do WhatsApp → Servidor próprio (storage local/S3)
- Conversão para formatos web-optimized (quando necessário)
- Geração de thumbnails (imagens/vídeos)
- URLs seguras (assinadas) quando aplicável

Metadados:
- tipo, tamanho, duração (quando aplicável)

Requisitos:
- Endpoints para servir mídia com permissão
- Limpeza de arquivos órfãos
- Observabilidade (logs e métricas de tempo de processamento)
