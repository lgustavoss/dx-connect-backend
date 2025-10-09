from .base import *  # noqa

# ==============================================================================
# PRODUÇÃO
# ==============================================================================

DEBUG = False

# ==============================================================================
# SEGURANÇA
# ==============================================================================

# HTTPS/SSL
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=True)

# Cookies seguros
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=True)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=True)

# Outras configurações de segurança
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# ==============================================================================
# CORS
# ==============================================================================

# Em produção, CORS_ALLOWED_ORIGINS DEVE ser configurado via variável de ambiente
# com os domínios reais do frontend
#
# Exemplo no .env de produção:
# CORS_ALLOWED_ORIGINS=https://app.dxconnect.com,https://www.dxconnect.com
#
# IMPORTANTE: NUNCA use CORS_ALLOW_ALL_ORIGINS=True em produção!


