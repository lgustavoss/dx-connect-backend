from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.db import transaction, models
from .models import Cliente, ContatoCliente, GrupoEmpresa


class ClienteSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Cliente (Empresa) com validações customizadas.
    """
    
    # Campos calculados (read-only)
    contatos_principais = serializers.ReadOnlyField()
    endereco_completo = serializers.ReadOnlyField()
    nome_display = serializers.ReadOnlyField()
    
    # Campos de grupo de empresa
    grupo_empresa_nome = serializers.CharField(
        source='grupo_empresa.nome',
        read_only=True,
        help_text="Nome do grupo de empresas"
    )
    
    class Meta:
        model = Cliente
        fields = [
            'id',
            'grupo_empresa',
            'grupo_empresa_nome',
            'razao_social',
            'nome_fantasia',
            'cnpj',
            'inscricao_estadual',
            'inscricao_municipal',
            'ramo_atividade',
            'regime_tributario',
            'responsavel_legal_nome',
            'responsavel_legal_cpf',
            'responsavel_legal_cargo',
            'email_principal',
            'telefone_principal',
            'endereco',
            'numero',
            'complemento',
            'bairro',
            'cidade',
            'estado',
            'cep',
            'logo',
            'assinatura_digital',
            'status',
            'observacoes',
            'criado_em',
            'atualizado_em',
            'criado_por',
            'atualizado_por',
            'contatos_principais',
            'endereco_completo',
            'nome_display',
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em', 'criado_por', 'atualizado_por']
    
    def validate_cnpj(self, value):
        """Valida CNPJ usando algoritmo padrão"""
        if not value:
            return value
        
        import re
        # Remove caracteres não numéricos
        cnpj_limpo = re.sub(r'[^0-9]', '', value)
        
        # Verifica se tem 14 dígitos
        if len(cnpj_limpo) != 14:
            raise serializers.ValidationError("CNPJ deve ter 14 dígitos")
        
        # Validação do algoritmo do CNPJ
        if not self._validar_cnpj(cnpj_limpo):
            raise serializers.ValidationError("CNPJ inválido")
        
        return cnpj_limpo
    
    def validate_responsavel_legal_cpf(self, value):
        """Valida CPF do responsável legal"""
        if not value:
            return value
        
        import re
        # Remove caracteres não numéricos
        cpf_limpo = re.sub(r'[^0-9]', '', value)
        
        # Verifica se tem 11 dígitos
        if len(cpf_limpo) != 11:
            raise serializers.ValidationError("CPF deve ter 11 dígitos")
        
        # Validação do algoritmo do CPF
        if not self._validar_cpf(cpf_limpo):
            raise serializers.ValidationError("CPF inválido")
        
        return cpf_limpo
    
    def _validar_cnpj(self, cnpj):
        """Valida CNPJ usando algoritmo padrão"""
        # Verifica se todos os dígitos são iguais
        if cnpj == cnpj[0] * 14:
            return False
        
        # Validação do primeiro dígito verificador
        sequencia = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * sequencia[i] for i in range(12))
        resto = soma % 11
        dv1 = 0 if resto < 2 else 11 - resto
        
        if int(cnpj[12]) != dv1:
            return False
        
        # Validação do segundo dígito verificador
        sequencia = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * sequencia[i] for i in range(13))
        resto = soma % 11
        dv2 = 0 if resto < 2 else 11 - resto
        
        return int(cnpj[13]) == dv2
    
    def _validar_cpf(self, cpf):
        """Valida CPF usando algoritmo padrão"""
        # Verifica se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            return False
        
        # Validação do primeiro dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto = soma % 11
        dv1 = 0 if resto < 2 else 11 - resto
        
        if int(cpf[9]) != dv1:
            return False
        
        # Validação do segundo dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto = soma % 11
        dv2 = 0 if resto < 2 else 11 - resto
        
        return int(cpf[10]) == dv2


class ClienteListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listagem de clientes.
    """
    
    contatos_principais = serializers.ReadOnlyField()
    grupo_empresa_nome = serializers.CharField(
        source='grupo_empresa.nome',
        read_only=True
    )
    
    class Meta:
        model = Cliente
        fields = [
            'id',
            'razao_social',
            'nome_fantasia',
            'cnpj',
            'status',
            'grupo_empresa_nome',
            'contatos_principais',
        ]
        read_only_fields = ['id']


class ClienteCreateSerializer(ClienteSerializer):
    """
    Serializer específico para criação de clientes.
    """
    class Meta(ClienteSerializer.Meta):
        pass


class ClienteUpdateSerializer(ClienteSerializer):
    """
    Serializer específico para atualização de clientes.
    """
    class Meta(ClienteSerializer.Meta):
        pass


class ContatoClienteSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo ContatoCliente.
    """
    
    cliente_nome = serializers.CharField(
        source='cliente.razao_social',
        read_only=True,
        help_text="Nome da empresa"
    )
    
    class Meta:
        model = ContatoCliente
        fields = [
            'id',
            'cliente',
            'cliente_nome',
            'nome',
            'cargo',
            'whatsapp',
            'email',
            'ativo',
            'criado_em',
            'atualizado_em',
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']
    
    def validate_whatsapp(self, value):
        """Valida formato do WhatsApp"""
        if not value:
            raise serializers.ValidationError("WhatsApp é obrigatório")
        
        import re
        # Remove caracteres não numéricos exceto +
        whatsapp_limpo = re.sub(r'[^\d+]', '', value)
        
        # Deve ter entre 10 e 15 dígitos (com código do país)
        if not re.match(r'^\+?1?\d{9,15}$', whatsapp_limpo):
            raise serializers.ValidationError(
                "Formato de WhatsApp inválido. Use: +5511999999999"
            )
        
        return whatsapp_limpo


class DadosCapturadosChatSerializer(serializers.Serializer):
    """
    Serializer para dados capturados do chat.
    
    Usado para pré-cadastro com dados que o sistema conseguiu extrair.
    """
    
    whatsapp = serializers.CharField(
        max_length=20,
        help_text="WhatsApp da pessoa (obrigatório)"
    )
    
    nome = serializers.CharField(
        max_length=255,
        help_text="Nome completo da pessoa"
    )
    
    cargo = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Cargo da pessoa na empresa (opcional)"
    )
    
    email = serializers.EmailField(
        required=False,
        allow_blank=True,
        help_text="E-mail da pessoa (opcional)"
    )
    
    empresa_nome = serializers.CharField(
        max_length=255,
        help_text="Nome da empresa onde a pessoa trabalha"
    )
    
    empresa_cnpj = serializers.CharField(
        max_length=18,
        required=False,
        allow_blank=True,
        help_text="CNPJ da empresa (opcional, será solicitado depois)"
    )
    
    grupo_empresa_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID do grupo de empresas (opcional)"
    )
    
    def validate_whatsapp(self, value):
        """Valida formato do WhatsApp"""
        if not value:
            raise serializers.ValidationError("WhatsApp é obrigatório")
        
        import re
        # Remove caracteres não numéricos exceto +
        whatsapp_limpo = re.sub(r'[^\d+]', '', value)
        
        # Deve ter entre 10 e 15 dígitos (com código do país)
        if not re.match(r'^\+?1?\d{9,15}$', whatsapp_limpo):
            raise serializers.ValidationError(
                "Formato de WhatsApp inválido. Use: +5511999999999"
            )
        
        return whatsapp_limpo
    
    def validate_empresa_cnpj(self, value):
        """Valida CNPJ se fornecido"""
        if not value:
            return value
        
        import re
        # Remove caracteres não numéricos
        cnpj_limpo = re.sub(r'[^0-9]', '', value)
        
        # Verifica se tem 14 dígitos
        if len(cnpj_limpo) != 14:
            raise serializers.ValidationError("CNPJ deve ter 14 dígitos")
        
        # Validação básica do algoritmo do CNPJ
        if not self._validar_cnpj(cnpj_limpo):
            raise serializers.ValidationError("CNPJ inválido")
        
        return cnpj_limpo
    
    def validate_grupo_empresa_id(self, value):
        """Valida se o grupo de empresas existe"""
        if value is None:
            return value
        
        try:
            GrupoEmpresa.objects.get(id=value, ativo=True)
        except GrupoEmpresa.DoesNotExist:
            raise serializers.ValidationError("Grupo de empresas não encontrado")
        
        return value
    
    def _validar_cnpj(self, cnpj):
        """Valida CNPJ usando algoritmo padrão"""
        # Verifica se todos os dígitos são iguais
        if cnpj == cnpj[0] * 14:
            return False
        
        # Validação do primeiro dígito verificador
        sequencia = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * sequencia[i] for i in range(12))
        resto = soma % 11
        dv1 = 0 if resto < 2 else 11 - resto
        
        if int(cnpj[12]) != dv1:
            return False
        
        # Validação do segundo dígito verificador
        sequencia = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * sequencia[i] for i in range(13))
        resto = soma % 11
        dv2 = 0 if resto < 2 else 11 - resto
        
        return int(cnpj[13]) == dv2
    
    def create(self, validated_data):
        """Cria contato e empresa em uma única operação"""
        with transaction.atomic():
            # Extrair dados da empresa
            empresa_nome = validated_data.pop('empresa_nome')
            empresa_cnpj = validated_data.pop('empresa_cnpj', '')
            grupo_empresa_id = validated_data.pop('grupo_empresa_id', None)
            
            # Buscar ou criar empresa
            empresa = self._buscar_ou_criar_empresa(
                empresa_nome, 
                empresa_cnpj, 
                grupo_empresa_id
            )
            
            # Criar contato
            contato = ContatoCliente.objects.create(
                cliente=empresa,
                **validated_data
            )
            
            return contato
    
    def _buscar_ou_criar_empresa(self, nome, cnpj, grupo_id):
        """Busca empresa existente ou cria nova"""
        # Se CNPJ foi fornecido, buscar por CNPJ
        if cnpj:
            try:
                return Cliente.objects.get(cnpj=cnpj)
            except Cliente.DoesNotExist:
                pass
        
        # Buscar por nome (razão social ou nome fantasia)
        try:
            return Cliente.objects.get(
                models.Q(razao_social__iexact=nome) | 
                models.Q(nome_fantasia__iexact=nome)
            )
        except Cliente.DoesNotExist:
            pass
        
        # Se não encontrou, criar nova empresa
        grupo = None
        if grupo_id:
            try:
                grupo = GrupoEmpresa.objects.get(id=grupo_id)
            except GrupoEmpresa.DoesNotExist:
                pass
        
        # Gerar CNPJ temporário se não fornecido
        if not cnpj:
            cnpj = f"00.000.000/{len(Cliente.objects.all()):04d}-00"
        
        return Cliente.objects.create(
            razao_social=nome,
            cnpj=cnpj,
            grupo_empresa=grupo,
            responsavel_legal_nome="A ser preenchido",
            responsavel_legal_cpf="000.000.000-00"
        )


class BuscaContatoSerializer(serializers.Serializer):
    """
    Serializer para buscar contato por WhatsApp.
    """
    
    whatsapp = serializers.CharField(
        max_length=20,
        help_text="WhatsApp para buscar"
    )
    
    def validate_whatsapp(self, value):
        """Valida formato do WhatsApp"""
        if not value:
            raise serializers.ValidationError("WhatsApp é obrigatório")
        
        import re
        # Remove caracteres não numéricos exceto +
        whatsapp_limpo = re.sub(r'[^\d+]', '', value)
        
        # Deve ter entre 10 e 15 dígitos (com código do país)
        if not re.match(r'^\+?1?\d{9,15}$', whatsapp_limpo):
            raise serializers.ValidationError(
                "Formato de WhatsApp inválido. Use: +5511999999999"
            )
        
        return whatsapp_limpo


class CadastroManualContatoSerializer(serializers.Serializer):
    """
    Serializer para cadastro manual de contato pelo atendente.
    
    Usado quando o atendente precisa cadastrar um novo contato.
    """
    
    whatsapp = serializers.CharField(
        max_length=20,
        help_text="WhatsApp da pessoa (obrigatório)"
    )
    
    nome = serializers.CharField(
        max_length=255,
        help_text="Nome completo da pessoa"
    )
    
    cargo = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Cargo da pessoa na empresa (opcional)"
    )
    
    email = serializers.EmailField(
        required=False,
        allow_blank=True,
        help_text="E-mail da pessoa (opcional)"
    )
    
    empresa_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID da empresa existente (se já cadastrada)"
    )
    
    empresa_nome = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Nome da empresa (se for nova)"
    )
    
    empresa_cnpj = serializers.CharField(
        max_length=18,
        required=False,
        allow_blank=True,
        help_text="CNPJ da empresa (opcional)"
    )
    
    grupo_empresa_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID do grupo de empresas (opcional)"
    )
    
    def validate_whatsapp(self, value):
        """Valida formato do WhatsApp"""
        if not value:
            raise serializers.ValidationError("WhatsApp é obrigatório")
        
        import re
        whatsapp_limpo = re.sub(r'[^\d+]', '', value)
        
        if not re.match(r'^\+?1?\d{9,15}$', whatsapp_limpo):
            raise serializers.ValidationError(
                "Formato de WhatsApp inválido. Use: +5511999999999"
            )
        
        return whatsapp_limpo
    
    def validate_empresa_cnpj(self, value):
        """Valida CNPJ se fornecido"""
        if not value:
            return value
        
        import re
        # Remove caracteres não numéricos
        cnpj_limpo = re.sub(r'[^0-9]', '', value)
        
        # Verifica se tem 14 dígitos
        if len(cnpj_limpo) != 14:
            raise serializers.ValidationError("CNPJ deve ter 14 dígitos")
        
        # Validação básica do algoritmo do CNPJ
        if not self._validar_cnpj(cnpj_limpo):
            raise serializers.ValidationError("CNPJ inválido")
        
        return cnpj_limpo
    
    def validate_grupo_empresa_id(self, value):
        """Valida se o grupo de empresas existe"""
        if value is None:
            return value
        
        try:
            GrupoEmpresa.objects.get(id=value, ativo=True)
        except GrupoEmpresa.DoesNotExist:
            raise serializers.ValidationError("Grupo de empresas não encontrado")
        
        return value
    
    def _validar_cnpj(self, cnpj):
        """Valida CNPJ usando algoritmo padrão"""
        # Verifica se todos os dígitos são iguais
        if cnpj == cnpj[0] * 14:
            return False
        
        # Validação do primeiro dígito verificador
        sequencia = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * sequencia[i] for i in range(12))
        resto = soma % 11
        dv1 = 0 if resto < 2 else 11 - resto
        
        if int(cnpj[12]) != dv1:
            return False
        
        # Validação do segundo dígito verificador
        sequencia = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * sequencia[i] for i in range(13))
        resto = soma % 11
        dv2 = 0 if resto < 2 else 11 - resto
        
        return int(cnpj[13]) == dv2
    
    def validate(self, attrs):
        """Validações gerais"""
        # Deve ter empresa_id OU empresa_nome
        if not attrs.get('empresa_id') and not attrs.get('empresa_nome'):
            raise serializers.ValidationError(
                "Deve informar empresa_id (empresa existente) ou empresa_nome (nova empresa)"
            )
        
        return attrs
    
    def create(self, validated_data):
        """Cria contato e empresa se necessário"""
        with transaction.atomic():
            # Buscar ou criar empresa
            if validated_data.get('empresa_id'):
                try:
                    empresa = Cliente.objects.get(id=validated_data['empresa_id'])
                except Cliente.DoesNotExist:
                    raise serializers.ValidationError({
                        'empresa_id': 'Empresa não encontrada'
                    })
            else:
                empresa = self._buscar_ou_criar_empresa(
                    validated_data.get('empresa_nome'),
                    validated_data.get('empresa_cnpj', ''),
                    validated_data.get('grupo_empresa_id')
                )
            
            # Criar contato
            contato = ContatoCliente.objects.create(
                cliente=empresa,
                whatsapp=validated_data['whatsapp'],
                nome=validated_data['nome'],
                cargo=validated_data.get('cargo', ''),
                email=validated_data.get('email', '')
            )
            
            return contato
    
    def _buscar_ou_criar_empresa(self, nome, cnpj, grupo_id):
        """Busca empresa existente ou cria nova"""
        # Se CNPJ foi fornecido, buscar por CNPJ
        if cnpj:
            try:
                return Cliente.objects.get(cnpj=cnpj)
            except Cliente.DoesNotExist:
                pass
        
        # Buscar por nome (razão social ou nome fantasia)
        try:
            return Cliente.objects.get(
                models.Q(razao_social__iexact=nome) | 
                models.Q(nome_fantasia__iexact=nome)
            )
        except Cliente.DoesNotExist:
            pass
        
        # Se não encontrou, criar nova empresa
        grupo = None
        if grupo_id:
            try:
                grupo = GrupoEmpresa.objects.get(id=grupo_id)
            except GrupoEmpresa.DoesNotExist:
                pass
        
        # Gerar CNPJ temporário se não fornecido
        if not cnpj:
            cnpj = f"00.000.000/{len(Cliente.objects.all()):04d}-00"
        
        return Cliente.objects.create(
            razao_social=nome,
            cnpj=cnpj,
            grupo_empresa=grupo,
            responsavel_legal_nome="A ser preenchido",
            responsavel_legal_cpf="000.000.000-00"
        )


class GrupoEmpresaSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo GrupoEmpresa.
    """
    
    empresas_count = serializers.SerializerMethodField()
    
    class Meta:
        model = GrupoEmpresa
        fields = [
            'id',
            'nome',
            'descricao',
            'ativo',
            'empresas_count',
            'criado_em',
            'atualizado_em',
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em', 'empresas_count']
    
    def get_empresas_count(self, obj):
        """Retorna o número de empresas no grupo"""
        return obj.empresas.count()