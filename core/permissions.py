from rest_framework.permissions import BasePermission


class HasDjangoPerm(BasePermission):
    required_perm: str = ""

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        perm = getattr(view, "required_perm", None) or self.required_perm
        return bool(perm and request.user.has_perm(perm))


class CanManageConfigCompany(HasDjangoPerm):
    required_perm = "core.manage_config_company"


class CanManageConfigChat(HasDjangoPerm):
    required_perm = "core.manage_config_chat"


class CanManageConfigEmail(HasDjangoPerm):
    required_perm = "core.manage_config_email"


class CanManageConfigAppearance(HasDjangoPerm):
    required_perm = "core.manage_config_appearance"


class CanManageConfigWhatsApp(HasDjangoPerm):
    required_perm = "core.manage_config_whatsapp"


