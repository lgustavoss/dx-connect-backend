from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


ROLE_DEFS = {
    "Atendente": [
        "core.view_config",
    ],
    "Supervisor": [
        "core.view_config",
        "core.manage_config_chat",
    ],
    "Gerente": [
        "core.view_config",
        "core.manage_config_company",
        "core.manage_config_chat",
        "core.manage_config_email",
        "core.manage_config_appearance",
        "core.manage_config_whatsapp",
    ],
}


class Command(BaseCommand):
    help = "Cria/atualiza grupos de função com permissões sugeridas (idempotente)"

    def handle(self, *args, **options):
        for role, codename_list in ROLE_DEFS.items():
            group, _ = Group.objects.get_or_create(name=role)
            perms = Permission.objects.filter(codename__in=[c.split(".")[-1] for c in codename_list], content_type__app_label__in=[c.split(".")[0] for c in codename_list if "." in c] or None)
            # fallback quando codename estiver no formato app.codename
            if not perms.exists():
                perms = Permission.objects.filter(codename__in=[c.split(".")[-1] for c in codename_list])
            group.permissions.set(perms)
            self.stdout.write(self.style.SUCCESS(f"Grupo '{role}' atualizado com {perms.count()} permissões"))


