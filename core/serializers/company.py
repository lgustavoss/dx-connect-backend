from rest_framework import serializers

from integrations.validators import validate_cnpj, validate_uf


class AddressSerializer(serializers.Serializer):
    cep = serializers.RegexField(r"^\d{8}$")
    logradouro = serializers.CharField(max_length=100)
    numero = serializers.CharField(max_length=10)
    complemento = serializers.CharField(max_length=50, allow_blank=True, required=False)
    bairro = serializers.CharField(max_length=50)
    cidade = serializers.CharField(max_length=50)
    uf = serializers.CharField(max_length=2)

    def validate_uf(self, value: str) -> str:
        validate_uf(value)
        return value


class CompanyDataSerializer(serializers.Serializer):
    razao_social = serializers.CharField(max_length=100)
    nome_fantasia = serializers.CharField(max_length=100)
    cnpj = serializers.CharField()
    inscricao_estadual = serializers.CharField(max_length=20)
    inscricao_municipal = serializers.CharField(max_length=20, allow_blank=True, required=False)
    regime_tributario = serializers.ChoiceField(choices=["1", "2", "3"]) 
    cnae_principal = serializers.CharField(max_length=10, allow_blank=True, required=False)
    telefone = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    site = serializers.CharField(max_length=100, allow_blank=True, required=False)
    endereco = AddressSerializer()

    def validate_cnpj(self, value: str) -> str:
        validate_cnpj(value)
        return value
