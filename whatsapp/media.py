"""
Modelos e serviços para processamento de mídias WhatsApp (Issue #46).

Suporta download, conversão, thumbnails e armazenamento seguro de mídias.
"""
from __future__ import annotations

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.files.base import ContentFile
from django.utils import timezone
import os
import uuid
import hashlib
from typing import Optional


class MediaFile(models.Model):
    """
    Modelo para armazenar metadados de arquivos de mídia do WhatsApp.
    
    Gerencia download, conversão, thumbnails e URLs seguras para mídias.
    """
    
    MEDIA_TYPE_CHOICES = [
        ('image', 'Imagem'),
        ('audio', 'Áudio'),
        ('video', 'Vídeo'),
        ('document', 'Documento'),
        ('sticker', 'Sticker'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('downloading', 'Baixando'),
        ('processing', 'Processando'),
        ('ready', 'Pronto'),
        ('error', 'Erro'),
    ]
    
    # Relacionamento com mensagem
    message = models.ForeignKey(
        'whatsapp.WhatsAppMessage',
        on_delete=models.CASCADE,
        related_name='media_files',
        verbose_name=_("Mensagem"),
        help_text=_("Mensagem WhatsApp associada")
    )
    
    # Identificação
    file_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name=_("ID do Arquivo")
    )
    
    # URLs originais
    original_url = models.URLField(
        max_length=1000,
        verbose_name=_("URL Original"),
        help_text=_("URL da mídia no WhatsApp")
    )
    
    # Tipo e metadados
    media_type = models.CharField(
        max_length=20,
        choices=MEDIA_TYPE_CHOICES,
        verbose_name=_("Tipo de Mídia")
    )
    
    mime_type = models.CharField(
        max_length=100,
        verbose_name=_("Tipo MIME")
    )
    
    file_size = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Tamanho (bytes)")
    )
    
    # Duração (para áudio/vídeo)
    duration_seconds = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Duração (segundos)")
    )
    
    # Dimensões (para imagem/vídeo)
    width = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Largura (px)")
    )
    
    height = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Altura (px)")
    )
    
    # Arquivos armazenados
    original_file = models.FileField(
        upload_to='whatsapp/media/original/%Y/%m/%d/',
        null=True,
        blank=True,
        verbose_name=_("Arquivo Original")
    )
    
    converted_file = models.FileField(
        upload_to='whatsapp/media/converted/%Y/%m/%d/',
        null=True,
        blank=True,
        verbose_name=_("Arquivo Convertido"),
        help_text=_("Versão otimizada para web")
    )
    
    thumbnail_file = models.ImageField(
        upload_to='whatsapp/media/thumbnails/%Y/%m/%d/',
        null=True,
        blank=True,
        verbose_name=_("Thumbnail")
    )
    
    # Hash para deduplicação
    file_hash = models.CharField(
        max_length=64,
        db_index=True,
        blank=True,
        verbose_name=_("Hash SHA-256"),
        help_text=_("Para evitar duplicatas")
    )
    
    # Status do processamento
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_("Status"),
        db_index=True
    )
    
    error_message = models.TextField(
        blank=True,
        verbose_name=_("Mensagem de Erro")
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Criado em")
    )
    
    downloaded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Baixado em")
    )
    
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Processado em")
    )
    
    # Métricas de tempo
    download_time_ms = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Tempo de Download (ms)")
    )
    
    processing_time_ms = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Tempo de Processamento (ms)")
    )
    
    # Controle de acesso
    is_public = models.BooleanField(
        default=False,
        verbose_name=_("Público"),
        help_text=_("Se True, não requer autenticação")
    )
    
    access_count = models.IntegerField(
        default=0,
        verbose_name=_("Contador de Acessos")
    )
    
    last_accessed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Último Acesso")
    )
    
    class Meta:
        app_label = 'whatsapp'
        verbose_name = _("Arquivo de Mídia")
        verbose_name_plural = _("Arquivos de Mídia")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['file_hash']),
            models.Index(fields=['message', 'media_type']),
        ]
    
    def __str__(self) -> str:
        return f"{self.get_media_type_display()} - {self.file_id} ({self.get_status_display()})"
    
    @property
    def total_processing_time_ms(self) -> Optional[int]:
        """Tempo total de processamento (download + conversão)"""
        if self.download_time_ms and self.processing_time_ms:
            return self.download_time_ms + self.processing_time_ms
        return None
    
    @property
    def file_size_mb(self) -> Optional[float]:
        """Tamanho do arquivo em MB"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return None
    
    @property
    def has_thumbnail(self) -> bool:
        """Verifica se tem thumbnail"""
        return bool(self.thumbnail_file)
    
    @property
    def has_converted(self) -> bool:
        """Verifica se tem versão convertida"""
        return bool(self.converted_file)
    
    def get_primary_file(self):
        """Retorna o arquivo principal (convertido se existir, senão original)"""
        return self.converted_file if self.converted_file else self.original_file
    
    def increment_access(self):
        """Incrementa contador de acesso"""
        self.access_count += 1
        self.last_accessed_at = timezone.now()
        self.save(update_fields=['access_count', 'last_accessed_at'])
    
    def mark_as_downloaded(self, download_time_ms: int):
        """Marca como baixado"""
        self.status = 'processing'
        self.downloaded_at = timezone.now()
        self.download_time_ms = download_time_ms
        self.save(update_fields=['status', 'downloaded_at', 'download_time_ms'])
    
    def mark_as_ready(self, processing_time_ms: int):
        """Marca como pronto"""
        self.status = 'ready'
        self.processed_at = timezone.now()
        self.processing_time_ms = processing_time_ms
        self.save(update_fields=['status', 'processed_at', 'processing_time_ms'])
    
    def mark_as_error(self, error_msg: str):
        """Marca como erro"""
        self.status = 'error'
        self.error_message = error_msg
        self.save(update_fields=['status', 'error_message'])
    
    def calculate_hash(self, file_content: bytes) -> str:
        """Calcula hash SHA-256 do conteúdo"""
        return hashlib.sha256(file_content).hexdigest()
    
    def generate_signed_url(self, expiration_seconds: int = 3600) -> str:
        """
        Gera URL assinada para acesso seguro.
        
        Args:
            expiration_seconds: Tempo de expiração em segundos (padrão: 1 hora)
        
        Returns:
            URL assinada com token
        """
        from django.core.signing import TimestampSigner
        
        signer = TimestampSigner()
        token = signer.sign(str(self.file_id))
        
        # Em produção, usar domínio real
        base_url = settings.MEDIA_URL
        return f"{base_url}whatsapp/media/secure/{self.file_id}/?token={token}"

