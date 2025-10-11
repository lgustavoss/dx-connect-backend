"""
Views para preferências de notificação (Issue #39).
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from .models_preferences import PreferenciasNotificacao
from .serializers_preferences import PreferenciasNotificacaoSerializer


class PreferenciasNotificacaoView(APIView):
    """
    View para gerenciar preferências de notificação do usuário.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Obter preferências de notificação",
        description="Retorna preferências de notificação do usuário autenticado",
        responses={200: PreferenciasNotificacaoSerializer}
    )
    def get(self, request):
        """Obtém preferências do usuário"""
        preferencias, created = PreferenciasNotificacao.objects.get_or_create(
            usuario=request.user
        )
        
        serializer = PreferenciasNotificacaoSerializer(preferencias)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        summary="Atualizar preferências de notificação",
        description="Atualiza preferências de notificação do usuário autenticado",
        request=PreferenciasNotificacaoSerializer,
        responses={200: PreferenciasNotificacaoSerializer}
    )
    def patch(self, request):
        """Atualiza preferências do usuário"""
        preferencias, created = PreferenciasNotificacao.objects.get_or_create(
            usuario=request.user
        )
        
        serializer = PreferenciasNotificacaoSerializer(
            preferencias,
            data=request.data,
            partial=True
        )
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_200_OK)

