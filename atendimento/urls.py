from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    DepartamentoViewSet,
    FilaAtendimentoViewSet,
    AtendimentoViewSet
)

router = DefaultRouter()
router.register(r'departamentos', DepartamentoViewSet, basename='departamento')
router.register(r'filas', FilaAtendimentoViewSet, basename='fila')
router.register(r'atendimentos', AtendimentoViewSet, basename='atendimento')

urlpatterns = [
    path('', include(router.urls)),
]

