from django.core.management.base import BaseCommand

from core.defaults import DEFAULT_CHAT_SETTINGS, DEFAULT_COMPANY_DATA, DEFAULT_EMAIL_SETTINGS
from core.models import Config


class Command(BaseCommand):
    help = "Inicializa a tabela Config com valores padrão se inexistente"

    def handle(self, *args, **options):
        obj, created = Config.objects.get_or_create()
        if created or not obj.company_data:
            obj.company_data = DEFAULT_COMPANY_DATA
        if created or not obj.chat_settings:
            obj.chat_settings = DEFAULT_CHAT_SETTINGS
        if created or not obj.email_settings:
            obj.email_settings = DEFAULT_EMAIL_SETTINGS
        obj.full_clean()
        obj.save()
        self.stdout.write(self.style.SUCCESS("Config inicializada."))
