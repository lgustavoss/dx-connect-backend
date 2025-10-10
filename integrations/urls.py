"""
URLs para integrações externas.
"""

from django.urls import path
from .views import CEPConsultaView

urlpatterns = [
    path('cep/<str:cep>/', CEPConsultaView.as_view(), name='cep-consulta'),
]

