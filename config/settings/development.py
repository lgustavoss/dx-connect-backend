from .base import *  # noqa

DEBUG = True


# CORS (desenvolvimento local)
# Frontend Vite: http://localhost:5173
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
# JWT por header Authorization → sem cookies/credenciais
CORS_ALLOW_CREDENTIALS = False

