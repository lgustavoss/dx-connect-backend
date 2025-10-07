from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClienteViewSet,
    ContatoClienteViewSet,
    ChatIntegrationView,
    CadastroManualView,
    GrupoEmpresaViewSet
)

# Router para ViewSets
router = DefaultRouter()
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'contatos', ContatoClienteViewSet, basename='contato')
router.register(r'grupos-empresa', GrupoEmpresaViewSet, basename='grupo-empresa')

# URLs do app clientes
urlpatterns = [
    # Integração com chat (acesso público) - URLs específicas primeiro
    path('clientes/chat/buscar-contato/', ChatIntegrationView.as_view({'post': 'buscar_contato'}), name='buscar-contato-chat'),
    path('clientes/chat/dados-capturados/', ChatIntegrationView.as_view({'post': 'dados_capturados'}), name='dados-capturados-chat'),
    # Cadastro manual pelo atendente (autenticado) - URLs específicas primeiro
    path('clientes/cadastro-manual/', CadastroManualView.as_view(), name='cadastro-manual'),
    # URLs do router (ViewSets) - por último para evitar conflitos
    path('', include(router.urls)),
]
