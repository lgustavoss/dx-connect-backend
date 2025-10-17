"""
Comando para processar retry de mensagens que falharam
"""
import asyncio
import logging
from django.core.management.base import BaseCommand
from whatsapp.message_status_service import get_message_status_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Processa retry de mensagens que falharam no envio'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra quais mensagens seriam processadas sem executar',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Número máximo de mensagens para processar',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('Modo dry-run ativado - nenhuma alteração será feita')
            )
        
        # Executar processamento assíncrono
        asyncio.run(self.process_retry(dry_run, limit))
    
    async def process_retry(self, dry_run: bool, limit: int):
        """Processa retry de mensagens"""
        try:
            service = get_message_status_service()
            
            if dry_run:
                # Em modo dry-run, apenas mostrar estatísticas
                stats = await service.get_message_stats()
                self.stdout.write(f"Estatísticas de mensagens:")
                self.stdout.write(f"  Total: {stats.get('total', 0)}")
                self.stdout.write(f"  Falharam: {stats.get('failed', 0)}")
                self.stdout.write(f"  Erro: {stats.get('error', 0)}")
                self.stdout.write(f"  Taxa de falha: {stats.get('failure_rate', 0)}%")
            else:
                # Processar retry real
                count = await service.retry_failed_messages()
                self.stdout.write(
                    self.style.SUCCESS(f'{count} mensagens marcadas para retry')
                )
                
        except Exception as e:
            logger.error(f"Erro ao processar retry: {e}")
            self.stdout.write(
                self.style.ERROR(f'Erro ao processar retry: {e}')
            )
