from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Agent


@admin.register(Agent)
class AgentAdmin(UserAdmin):
    model = Agent
    list_display = ("id", "username", "email", "display_name", "is_active", "is_staff")
    fieldsets = UserAdmin.fieldsets + (
        ("Dados do agente", {"fields": ("display_name", "phone_number")}),
    )

