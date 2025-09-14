from typing import Tuple

from core.defaults import (
    DEFAULT_CHAT_SETTINGS,
    DEFAULT_COMPANY_DATA,
    DEFAULT_EMAIL_SETTINGS,
    DEFAULT_APPEARANCE_SETTINGS,
)
from core.models import Config


def get_or_create_config_with_defaults() -> Tuple[Config, bool]:
    obj, created = Config.objects.get_or_create()
    changed = False
    if not obj.company_data:
        obj.company_data = DEFAULT_COMPANY_DATA
        changed = True
    if not obj.chat_settings:
        obj.chat_settings = DEFAULT_CHAT_SETTINGS
        changed = True
    if not obj.email_settings:
        obj.email_settings = DEFAULT_EMAIL_SETTINGS
        changed = True
    if not getattr(obj, "appearance_settings", None):
        obj.appearance_settings = DEFAULT_APPEARANCE_SETTINGS
        changed = True
    if changed:
        obj.full_clean()
        obj.save()
    return obj, created


