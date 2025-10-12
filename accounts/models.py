from django.contrib.auth.models import AbstractUser
from django.db import models

# Importar modelos de preferências e presença
from .models_preferences import PreferenciasNotificacao
from .models_presence import AgentPresence, TypingIndicator


class Agent(AbstractUser):
    display_name = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.display_name or self.username

    class Meta(AbstractUser.Meta):
        permissions = (
            ("manage_auth", "Pode gerenciar autenticação (grupos e permissões)"),
        )

