import django_filters
from django.db.models import Q
from .models import Cliente, ContatoCliente, DocumentoCliente


class ClienteFilter(django_filters.FilterSet):
    """
    Filtros para o modelo Cliente (Pessoa Jurídica).
    
    Filtros disponíveis:
    - razao_social: busca por razão social (icontains)
    - nome_fantasia: busca por nome fantasia (icontains)
    - cnpj: busca por CNPJ (icontains)
    - status: filtro exato por status
    - regime_tributario: filtro exato por regime tributário
    - cidade: busca por cidade (icontains)
    - estado: filtro exato por estado
    - email_principal: busca por email principal (icontains)
    - telefone_principal: busca por telefone principal (icontains)
    - ramo_atividade: busca por ramo de atividade (icontains)
    - criado_apos: clientes criados após data
    - criado_antes: clientes criados antes de data
    - atualizado_apos: clientes atualizados após data
    - atualizado_antes: clientes atualizados antes de data
    """
    
    # Filtros de texto
    razao_social = django_filters.CharFilter(
        field_name='razao_social',
        lookup_expr='icontains',
        help_text='Busca por razão social (contém)'
    )
    
    nome_fantasia = django_filters.CharFilter(
        field_name='nome_fantasia',
        lookup_expr='icontains',
        help_text='Busca por nome fantasia (contém)'
    )
    
    cnpj = django_filters.CharFilter(
        field_name='cnpj',
        lookup_expr='icontains',
        help_text='Busca por CNPJ (contém)'
    )
    
    email_principal = django_filters.CharFilter(
        field_name='email_principal',
        lookup_expr='icontains',
        help_text='Busca por email principal (contém)'
    )
    
    telefone_principal = django_filters.CharFilter(
        field_name='telefone_principal',
        lookup_expr='icontains',
        help_text='Busca por telefone principal (contém)'
    )
    
    cidade = django_filters.CharFilter(
        field_name='cidade',
        lookup_expr='icontains',
        help_text='Busca por cidade (contém)'
    )
    
    ramo_atividade = django_filters.CharFilter(
        field_name='ramo_atividade',
        lookup_expr='icontains',
        help_text='Busca por ramo de atividade (contém)'
    )
    
    # Filtros de seleção
    status = django_filters.ChoiceFilter(
        choices=Cliente.STATUS_CHOICES,
        help_text='Filtro por status'
    )
    
    regime_tributario = django_filters.ChoiceFilter(
        choices=Cliente.REGIME_TRIBUTARIO_CHOICES,
        help_text='Filtro por regime tributário'
    )
    
    estado = django_filters.CharFilter(
        field_name='estado',
        lookup_expr='iexact',
        help_text='Filtro por estado (exato)'
    )
    
    # Filtros de data
    criado_apos = django_filters.DateTimeFilter(
        field_name='criado_em',
        lookup_expr='gte',
        help_text='Clientes criados após esta data'
    )
    
    criado_antes = django_filters.DateTimeFilter(
        field_name='criado_em',
        lookup_expr='lte',
        help_text='Clientes criados antes desta data'
    )
    
    atualizado_apos = django_filters.DateTimeFilter(
        field_name='atualizado_em',
        lookup_expr='gte',
        help_text='Clientes atualizados após esta data'
    )
    
    atualizado_antes = django_filters.DateTimeFilter(
        field_name='atualizado_em',
        lookup_expr='lte',
        help_text='Clientes atualizados antes desta data'
    )
    
    # Filtros combinados
    busca_geral = django_filters.CharFilter(
        method='filter_busca_geral',
        help_text='Busca geral em razão social, nome fantasia, CNPJ e contatos'
    )
    
    def filter_busca_geral(self, queryset, name, value):
        """
        Busca geral em múltiplos campos.
        """
        if not value:
            return queryset
        
        return queryset.filter(
            Q(razao_social__icontains=value) |
            Q(nome_fantasia__icontains=value) |
            Q(cnpj__icontains=value) |
            Q(email_principal__icontains=value) |
            Q(telefone_principal__icontains=value) |
            Q(ramo_atividade__icontains=value) |
            Q(responsavel_legal_nome__icontains=value)
        )
    
    class Meta:
        model = Cliente
        fields = [
            'razao_social',
            'nome_fantasia',
            'cnpj',
            'status',
            'regime_tributario',
            'cidade',
            'estado',
            'email_principal',
            'telefone_principal',
            'ramo_atividade',
            'criado_apos',
            'criado_antes',
            'atualizado_apos',
            'atualizado_antes',
            'busca_geral',
        ]


class ContatoClienteFilter(django_filters.FilterSet):
    """
    Filtros para o modelo ContatoCliente.
    
    Filtros disponíveis:
    - cliente: filtro por ID do cliente
    - nome: busca por nome (icontains)
    - whatsapp: busca por WhatsApp (icontains)
    - email: busca por email (icontains)
    - cargo: busca por cargo (icontains)
    - ativo: filtro por status ativo
    """
    
    cliente = django_filters.NumberFilter(
        field_name='cliente',
        help_text='Filtro por ID do cliente'
    )
    
    nome = django_filters.CharFilter(
        field_name='nome',
        lookup_expr='icontains',
        help_text='Busca por nome (contém)'
    )
    
    whatsapp = django_filters.CharFilter(
        field_name='whatsapp',
        lookup_expr='icontains',
        help_text='Busca por WhatsApp (contém)'
    )
    
    email = django_filters.CharFilter(
        field_name='email',
        lookup_expr='icontains',
        help_text='Busca por email (contém)'
    )
    
    cargo = django_filters.CharFilter(
        field_name='cargo',
        lookup_expr='icontains',
        help_text='Busca por cargo (contém)'
    )
    
    ativo = django_filters.BooleanFilter(
        field_name='ativo',
        help_text='Filtro por status ativo'
    )
    
    class Meta:
        model = ContatoCliente
        fields = [
            'cliente',
            'nome',
            'whatsapp',
            'email',
            'cargo',
            'ativo',
        ]


class DocumentoClienteFilter(django_filters.FilterSet):
    """
    Filtros para o modelo DocumentoCliente.
    
    Filtros disponíveis:
    - cliente: filtro por ID do cliente
    - nome: busca por nome (icontains)
    - tipo_documento: filtro por tipo de documento
    - status: filtro por status do documento
    - origem: filtro por origem (manual/gerado/importado)
    - template_usado: busca por template usado (icontains)
    - data_upload_apos: documentos enviados após data
    - data_upload_antes: documentos enviados antes de data
    - data_vencimento_apos: documentos com vencimento após data
    - data_vencimento_antes: documentos com vencimento antes de data
    - ativo: filtro por status ativo
    """
    
    cliente = django_filters.NumberFilter(
        field_name='cliente',
        help_text='Filtro por ID do cliente'
    )
    
    nome = django_filters.CharFilter(
        field_name='nome',
        lookup_expr='icontains',
        help_text='Busca por nome (contém)'
    )
    
    tipo_documento = django_filters.ChoiceFilter(
        choices=DocumentoCliente.TIPO_DOCUMENTO_CHOICES,
        help_text='Filtro por tipo de documento'
    )
    
    status = django_filters.ChoiceFilter(
        choices=DocumentoCliente.STATUS_DOCUMENTO_CHOICES,
        help_text='Filtro por status do documento'
    )
    
    origem = django_filters.ChoiceFilter(
        choices=DocumentoCliente.ORIGEM_DOCUMENTO_CHOICES,
        help_text='Filtro por origem do documento'
    )
    
    template_usado = django_filters.CharFilter(
        field_name='template_usado',
        lookup_expr='icontains',
        help_text='Busca por template usado (contém)'
    )
    
    data_upload_apos = django_filters.DateFilter(
        field_name='data_upload__date',
        lookup_expr='gte',
        help_text='Documentos enviados após esta data'
    )
    
    data_upload_antes = django_filters.DateFilter(
        field_name='data_upload__date',
        lookup_expr='lte',
        help_text='Documentos enviados antes desta data'
    )
    
    data_vencimento_apos = django_filters.DateFilter(
        field_name='data_vencimento',
        lookup_expr='gte',
        help_text='Documentos com vencimento após esta data'
    )
    
    data_vencimento_antes = django_filters.DateFilter(
        field_name='data_vencimento',
        lookup_expr='lte',
        help_text='Documentos com vencimento antes desta data'
    )
    
    ativo = django_filters.BooleanFilter(
        field_name='ativo',
        help_text='Filtro por status ativo'
    )
    
    class Meta:
        model = DocumentoCliente
        fields = [
            'cliente',
            'nome',
            'tipo_documento',
            'status',
            'origem',
            'template_usado',
            'ativo',
        ]
