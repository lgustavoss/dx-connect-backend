"""
Views para integrações externas.
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from .cep_service import CEPService

logger = logging.getLogger(__name__)


class CEPConsultaView(APIView):
    """
    View para consulta de CEP usando a API ViaCEP.
    
    Este endpoint é público (não requer autenticação) para facilitar
    a integração com formulários de cadastro.
    """
    
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Consultar CEP",
        description="Consulta informações de endereço pelo CEP usando a API ViaCEP",
        parameters=[
            OpenApiParameter(
                name='cep',
                description='CEP no formato 12345678 ou 12345-678',
                required=True,
                type=str,
                location=OpenApiParameter.PATH
            )
        ],
        responses={
            200: OpenApiResponse(
                description="CEP encontrado com sucesso",
                response={
                    'type': 'object',
                    'properties': {
                        'cep': {'type': 'string', 'example': '01001-000'},
                        'logradouro': {'type': 'string', 'example': 'Praça da Sé'},
                        'complemento': {'type': 'string', 'example': 'lado ímpar'},
                        'bairro': {'type': 'string', 'example': 'Sé'},
                        'cidade': {'type': 'string', 'example': 'São Paulo'},
                        'estado': {'type': 'string', 'example': 'SP'},
                        'localidade': {'type': 'string', 'example': 'São Paulo'},
                        'uf': {'type': 'string', 'example': 'SP'},
                        'ibge': {'type': 'string', 'example': '3550308'},
                    }
                }
            ),
            400: OpenApiResponse(description="CEP inválido"),
            404: OpenApiResponse(description="CEP não encontrado"),
            500: OpenApiResponse(description="Erro ao consultar API externa"),
        },
        tags=['Integrações']
    )
    def get(self, request, cep):
        """
        Consulta informações de endereço pelo CEP.
        
        GET /api/v1/integrations/cep/{cep}/
        """
        try:
            # Consultar CEP
            data = CEPService.consultar_cep(cep)
            
            if not data:
                return Response({
                    'error': 'CEP não encontrado',
                    'message': 'O CEP informado não foi encontrado na base de dados'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Adicionar campos extras para facilitar uso no frontend
            response_data = {
                **data,
                'cidade': data.get('localidade'),  # Alias
                'estado': data.get('uf'),  # Alias
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.warning(f"CEP inválido fornecido: {cep}")
            return Response({
                'error': 'CEP inválido',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erro ao consultar CEP {cep}: {str(e)}")
            return Response({
                'error': 'Erro ao consultar CEP',
                'message': 'Não foi possível consultar o CEP. Tente novamente mais tarde.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

