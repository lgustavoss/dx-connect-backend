"""
Serviço de integração com API ViaCEP para consulta de endereços por CEP.

API: https://viacep.com.br/
"""

import logging
import requests
from typing import Dict, Optional
from django.core.cache import cache

logger = logging.getLogger(__name__)


class CEPService:
    """
    Serviço para consulta de CEP usando a API ViaCEP.
    
    Funcionalidades:
    - Consulta de CEP com cache
    - Validação de formato
    - Tratamento de erros
    - Timeout configurável
    """
    
    BASE_URL = "https://viacep.com.br/ws"
    CACHE_TIMEOUT = 86400  # 24 horas
    REQUEST_TIMEOUT = 5  # 5 segundos
    
    @classmethod
    def consultar_cep(cls, cep: str) -> Optional[Dict[str, str]]:
        """
        Consulta informações de endereço pelo CEP.
        
        Args:
            cep: CEP no formato '12345678' ou '12345-678'
            
        Returns:
            Dicionário com informações do endereço ou None se não encontrado
            {
                'cep': '01001-000',
                'logradouro': 'Praça da Sé',
                'complemento': 'lado ímpar',
                'bairro': 'Sé',
                'localidade': 'São Paulo',
                'uf': 'SP',
                'ibge': '3550308',
                'gia': '1004',
                'ddd': '11',
                'siafi': '7107'
            }
            
        Raises:
            ValueError: Se o CEP estiver em formato inválido
            requests.exceptions.RequestException: Se houver erro na requisição
        """
        # Limpar CEP (remover caracteres não numéricos)
        cep_limpo = cls._limpar_cep(cep)
        
        # Validar formato
        if not cls._validar_cep(cep_limpo):
            raise ValueError(f"CEP inválido: {cep}")
        
        # Verificar cache
        cache_key = f"cep:{cep_limpo}"
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info(f"CEP {cep_limpo} encontrado no cache")
            return cached_data
        
        # Consultar API
        try:
            logger.info(f"Consultando CEP {cep_limpo} na API ViaCEP")
            url = f"{cls.BASE_URL}/{cep_limpo}/json/"
            
            response = requests.get(url, timeout=cls.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            # Verificar se o CEP existe
            if data.get('erro'):
                logger.warning(f"CEP {cep_limpo} não encontrado na base de dados")
                return None
            
            # Armazenar no cache
            cache.set(cache_key, data, cls.CACHE_TIMEOUT)
            logger.info(f"CEP {cep_limpo} consultado com sucesso e armazenado no cache")
            
            return data
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout ao consultar CEP {cep_limpo}")
            raise requests.exceptions.RequestException("Timeout ao consultar CEP. Tente novamente.")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao consultar CEP {cep_limpo}: {str(e)}")
            raise
    
    @classmethod
    def _limpar_cep(cls, cep: str) -> str:
        """
        Remove caracteres não numéricos do CEP.
        
        Args:
            cep: CEP com ou sem formatação
            
        Returns:
            CEP apenas com números
        """
        import re
        return re.sub(r'\D', '', cep)
    
    @classmethod
    def _validar_cep(cls, cep: str) -> bool:
        """
        Valida se o CEP tem 8 dígitos.
        
        Args:
            cep: CEP limpo (apenas números)
            
        Returns:
            True se válido, False caso contrário
        """
        return len(cep) == 8 and cep.isdigit()
    
    @classmethod
    def formatar_endereco(cls, data: Dict[str, str]) -> Dict[str, str]:
        """
        Formata os dados retornados da API para o formato do modelo Cliente.
        
        Args:
            data: Dados retornados da API ViaCEP
            
        Returns:
            Dicionário formatado para o modelo Cliente
        """
        return {
            'endereco': data.get('logradouro', ''),
            'bairro': data.get('bairro', ''),
            'cidade': data.get('localidade', ''),
            'estado': data.get('uf', ''),
            'cep': data.get('cep', '').replace('-', ''),
            'complemento': data.get('complemento', ''),
        }


# Função auxiliar para uso rápido
def buscar_cep(cep: str) -> Optional[Dict[str, str]]:
    """
    Função auxiliar para buscar CEP.
    
    Args:
        cep: CEP no formato '12345678' ou '12345-678'
        
    Returns:
        Dicionário com informações do endereço ou None se não encontrado
    """
    return CEPService.consultar_cep(cep)

