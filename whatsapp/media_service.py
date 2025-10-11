"""
Serviço de processamento de mídias WhatsApp (Issue #46).

Responsável por download, conversão, thumbnails e armazenamento de mídias.
"""
import logging
import requests
import io
from typing import Optional, Dict, Tuple
from django.core.files.base import ContentFile
from django.utils import timezone
from PIL import Image
import os

from .media import MediaFile
from .models import WhatsAppMessage

logger = logging.getLogger(__name__)


class MediaProcessingService:
    """
    Serviço para processamento de mídias do WhatsApp.
    
    Funcionalidades:
    - Download de mídia
    - Geração de thumbnails
    - Conversão para formatos web-optimized
    - Cálculo de métricas
    """
    
    # Configurações
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    THUMBNAIL_SIZE = (300, 300)
    REQUEST_TIMEOUT = 30  # segundos
    
    # Formatos suportados para conversão
    IMAGE_FORMATS = {
        'image/jpeg': '.jpg',
        'image/png': '.png',
        'image/gif': '.gif',
        'image/webp': '.webp',
    }
    
    @classmethod
    def download_media(cls, url: str, message: WhatsAppMessage) -> Optional[MediaFile]:
        """
        Baixa mídia do WhatsApp e cria registro no banco.
        
        Args:
            url: URL da mídia
            message: Mensagem WhatsApp associada
        
        Returns:
            MediaFile ou None se falhar
        """
        start_time = timezone.now()
        
        try:
            logger.info(f"Baixando mídia: {url}")
            
            # Faz download
            response = requests.get(url, timeout=cls.REQUEST_TIMEOUT, stream=True)
            response.raise_for_status()
            
            # Verifica tamanho
            content_length = int(response.headers.get('content-length', 0))
            if content_length > cls.MAX_FILE_SIZE:
                logger.warning(f"Arquivo muito grande: {content_length} bytes")
                return None
            
            # Lê conteúdo
            content = response.content
            
            # Calcula tempo de download
            download_time_ms = int((timezone.now() - start_time).total_seconds() * 1000)
            
            # Determina tipo de mídia
            content_type = response.headers.get('content-type', '')
            media_type = cls._determine_media_type(content_type)
            
            # Cria registro no banco
            media_file = MediaFile.objects.create(
                message=message,
                original_url=url,
                media_type=media_type,
                mime_type=content_type,
                file_size=len(content),
                status='downloading'
            )
            
            # Calcula hash
            file_hash = media_file.calculate_hash(content)
            media_file.file_hash = file_hash
            
            # Salva arquivo original
            filename = f"{media_file.file_id}{cls._get_extension(content_type)}"
            media_file.original_file.save(
                filename,
                ContentFile(content),
                save=False
            )
            
            # Marca como baixado
            media_file.mark_as_downloaded(download_time_ms)
            
            logger.info(
                f"Mídia baixada com sucesso: {media_file.file_id} "
                f"({media_file.file_size_mb} MB, {download_time_ms}ms)"
            )
            
            return media_file
        
        except requests.exceptions.Timeout:
            logger.error(f"Timeout ao baixar mídia: {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao baixar mídia {url}: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao baixar mídia: {e}", exc_info=True)
            return None
    
    @classmethod
    def process_media(cls, media_file: MediaFile) -> bool:
        """
        Processa mídia (gera thumbnail e converte se necessário).
        
        Args:
            media_file: Arquivo de mídia para processar
        
        Returns:
            True se sucesso, False caso contrário
        """
        start_time = timezone.now()
        
        try:
            logger.info(f"Processando mídia: {media_file.file_id}")
            
            # Processa conforme o tipo
            if media_file.media_type == 'image':
                cls._process_image(media_file)
            elif media_file.media_type == 'video':
                cls._generate_video_thumbnail(media_file)
            # Áudio e documentos não precisam de processamento especial
            
            # Calcula tempo de processamento
            processing_time_ms = int((timezone.now() - start_time).total_seconds() * 1000)
            
            # Marca como pronto
            media_file.mark_as_ready(processing_time_ms)
            
            logger.info(
                f"Mídia processada com sucesso: {media_file.file_id} "
                f"({processing_time_ms}ms)"
            )
            
            return True
        
        except Exception as e:
            error_msg = f"Erro ao processar mídia: {str(e)}"
            logger.error(error_msg, exc_info=True)
            media_file.mark_as_error(error_msg)
            return False
    
    @classmethod
    def _process_image(cls, media_file: MediaFile):
        """Processa imagem: gera thumbnail e converte para formato otimizado"""
        # Abre imagem original
        media_file.original_file.open('rb')
        img = Image.open(media_file.original_file)
        
        # Salva dimensões
        media_file.width, media_file.height = img.size
        
        # Converte para RGB se necessário (para JPEG)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Gera thumbnail
        cls._generate_thumbnail(media_file, img)
        
        # Converte para formato otimizado (JPEG com qualidade 85)
        if media_file.mime_type != 'image/jpeg':
            cls._convert_image_to_jpeg(media_file, img)
        
        media_file.original_file.close()
        media_file.save()
    
    @classmethod
    def _generate_thumbnail(cls, media_file: MediaFile, img: Image.Image):
        """Gera thumbnail da imagem"""
        # Cria cópia para thumbnail
        thumb = img.copy()
        thumb.thumbnail(cls.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        
        # Salva thumbnail
        thumb_io = io.BytesIO()
        thumb.save(thumb_io, format='JPEG', quality=80, optimize=True)
        thumb_io.seek(0)
        
        thumbnail_filename = f"{media_file.file_id}_thumb.jpg"
        media_file.thumbnail_file.save(
            thumbnail_filename,
            ContentFile(thumb_io.read()),
            save=False
        )
        
        logger.debug(f"Thumbnail gerado: {thumbnail_filename}")
    
    @classmethod
    def _convert_image_to_jpeg(cls, media_file: MediaFile, img: Image.Image):
        """Converte imagem para JPEG otimizado"""
        # Salva como JPEG otimizado
        converted_io = io.BytesIO()
        img.save(converted_io, format='JPEG', quality=85, optimize=True)
        converted_io.seek(0)
        
        converted_filename = f"{media_file.file_id}_optimized.jpg"
        media_file.converted_file.save(
            converted_filename,
            ContentFile(converted_io.read()),
            save=False
        )
        
        logger.debug(f"Imagem convertida para JPEG: {converted_filename}")
    
    @classmethod
    def _generate_video_thumbnail(cls, media_file: MediaFile):
        """
        Gera thumbnail de vídeo (placeholder simples).
        
        Nota: Para produção, usar ffmpeg para extrair frame do vídeo.
        """
        # TODO: Implementar extração de frame com ffmpeg
        # Por enquanto, não gera thumbnail para vídeos
        logger.info(f"Thumbnail de vídeo não implementado: {media_file.file_id}")
        pass
    
    @classmethod
    def _determine_media_type(cls, content_type: str) -> str:
        """Determina tipo de mídia pelo content-type"""
        if content_type.startswith('image/'):
            return 'image'
        elif content_type.startswith('audio/'):
            return 'audio'
        elif content_type.startswith('video/'):
            return 'video'
        else:
            return 'document'
    
    @classmethod
    def _get_extension(cls, content_type: str) -> str:
        """Retorna extensão do arquivo baseado no content-type"""
        extensions = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'audio/mpeg': '.mp3',
            'audio/ogg': '.ogg',
            'video/mp4': '.mp4',
            'video/webm': '.webm',
            'application/pdf': '.pdf',
        }
        return extensions.get(content_type, '.bin')


def get_media_processing_service() -> MediaProcessingService:
    """Retorna instância do serviço de processamento de mídia"""
    return MediaProcessingService()

