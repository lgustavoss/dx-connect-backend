from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class GrupoEmpresa(models.Model):
    """
    Modelo para representar grupos de empresas.
    
    Exemplo: Grupo Google (Google Drive, Gmail, YouTube, etc.)
    """
    
    nome = models.CharField(
        max_length=255,
        verbose_name="Nome do Grupo",
        help_text="Nome do grupo de empresas"
    )
    
    descricao = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descrição",
        help_text="Descrição do grupo"
    )
    
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Se o grupo está ativo"
    )
    
    # Auditoria
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )
    
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em"
    )
    
    criado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='grupos_criados',
        verbose_name="Criado por"
    )
    
    class Meta:
        verbose_name = "Grupo de Empresas"
        verbose_name_plural = "Grupos de Empresas"
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class Cliente(models.Model):
    """
    Modelo para representar empresas clientes do sistema.
    
    Cada empresa pode ter múltiplos contatos (pessoas que trabalham nela).
    Uma empresa pode pertencer a um grupo de empresas.
    """
    
    # Opções para status do cliente
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo'),
        ('suspenso', 'Suspenso'),
        ('bloqueado', 'Bloqueado'),
    ]
    
    # Opções para regime tributário
    REGIME_TRIBUTARIO_CHOICES = [
        ('simples_nacional', 'Simples Nacional'),
        ('lucro_presumido', 'Lucro Presumido'),
        ('lucro_real', 'Lucro Real'),
        ('mei', 'MEI - Microempreendedor Individual'),
        ('outro', 'Outro'),
    ]
    
    # Relacionamento com grupo (opcional)
    grupo_empresa = models.ForeignKey(
        GrupoEmpresa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='empresas',
        verbose_name="Grupo de Empresas",
        help_text="Grupo ao qual a empresa pertence (opcional)"
    )
    
    # Campos básicos da empresa
    razao_social = models.CharField(
        max_length=255,
        verbose_name="Razão Social",
        help_text="Razão social da empresa",
        default="Empresa Temporária"
    )
    
    nome_fantasia = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Nome Fantasia",
        help_text="Nome fantasia da empresa"
    )
    
    cnpj = models.CharField(
        max_length=18,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$',
                message="CNPJ deve estar no formato: 12.345.678/0001-90"
            )
        ],
        verbose_name="CNPJ",
        help_text="CNPJ da empresa",
        default="00.000.000/0000-00"
    )
    
    # Campos específicos para PJ
    inscricao_estadual = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Inscrição Estadual",
        help_text="Inscrição estadual da empresa"
    )
    
    inscricao_municipal = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Inscrição Municipal",
        help_text="Inscrição municipal da empresa"
    )
    
    ramo_atividade = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Ramo de Atividade",
        help_text="Ramo de atividade da empresa"
    )
    
    regime_tributario = models.CharField(
        max_length=20,
        choices=REGIME_TRIBUTARIO_CHOICES,
        default='simples_nacional',
        verbose_name="Regime Tributário",
        help_text="Regime tributário da empresa"
    )
    
    # Responsável legal
    responsavel_legal_nome = models.CharField(
        max_length=255,
        verbose_name="Nome do Responsável Legal",
        help_text="Nome completo do responsável legal da empresa",
        default="Responsável Temporário"
    )
    
    responsavel_legal_cpf = models.CharField(
        max_length=14,
        validators=[
            RegexValidator(
                regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$',
                message="CPF deve estar no formato: 123.456.789-00"
            )
        ],
        verbose_name="CPF do Responsável Legal",
        help_text="CPF do responsável legal",
        default="000.000.000-00"
    )
    
    responsavel_legal_cargo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Cargo do Responsável Legal",
        help_text="Cargo do responsável legal na empresa"
    )
    
    # Contato principal da empresa (opcional)
    email_principal = models.EmailField(
        blank=True,
        null=True,
        verbose_name="E-mail Principal",
        help_text="E-mail principal da empresa"
    )
    
    telefone_principal = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Formato de telefone inválido. Use: +5511999999999"
            )
        ],
        verbose_name="Telefone Principal",
        help_text="Telefone principal da empresa"
    )
    
    # Endereço
    endereco = models.TextField(
        blank=True,
        null=True,
        verbose_name="Endereço",
        help_text="Endereço completo da empresa"
    )
    
    numero = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name="Número",
        help_text="Número do endereço"
    )
    
    complemento = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Complemento",
        help_text="Complemento do endereço (sala, andar, etc.)"
    )
    
    bairro = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Bairro",
        help_text="Bairro da empresa"
    )
    
    cidade = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Cidade",
        help_text="Cidade da empresa"
    )
    
    estado = models.CharField(
        max_length=2,
        blank=True,
        null=True,
        verbose_name="Estado",
        help_text="Estado (UF) da empresa"
    )
    
    cep = models.CharField(
        max_length=9,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\d{5}-?\d{3}$',
                message="CEP deve ter 8 dígitos. Use: 12345-678 ou 12345678"
            )
        ],
        verbose_name="CEP",
        help_text="CEP do endereço"
    )
    
    # Documentação
    logo = models.ImageField(
        upload_to='clientes/logos/',
        blank=True,
        null=True,
        verbose_name="Logo da Empresa",
        help_text="Logo da empresa"
    )
    
    assinatura_digital = models.ImageField(
        upload_to='clientes/assinaturas/',
        blank=True,
        null=True,
        verbose_name="Assinatura Digital",
        help_text="Assinatura digital do responsável legal"
    )
    
    # Status e controle
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ativo',
        verbose_name="Status",
        help_text="Status atual da empresa"
    )
    
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações",
        help_text="Observações adicionais sobre a empresa"
    )
    
    # Auditoria
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
        help_text="Data e hora de criação do registro"
    )
    
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em",
        help_text="Data e hora da última atualização"
    )
    
    criado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clientes_criados',
        verbose_name="Criado por",
        help_text="Usuário que criou o registro"
    )
    
    atualizado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clientes_atualizados',
        verbose_name="Atualizado por",
        help_text="Usuário que fez a última atualização"
    )
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['cnpj']),
            models.Index(fields=['razao_social']),
            models.Index(fields=['nome_fantasia']),
            models.Index(fields=['status']),
            models.Index(fields=['criado_em']),
        ]
    
    def __str__(self):
        return f"{self.razao_social} ({self.cnpj})"
    
    def clean(self):
        """Validações customizadas do modelo"""
        from django.core.exceptions import ValidationError
        
        # Validar CNPJ
        if self.cnpj and not self._validar_cnpj(self.cnpj):
            raise ValidationError({'cnpj': 'CNPJ inválido'})
        
        # Validar CPF do responsável legal
        if self.responsavel_legal_cpf and not self._validar_cpf(self.responsavel_legal_cpf):
            raise ValidationError({'responsavel_legal_cpf': 'CPF inválido'})
    
    def _validar_cpf(self, cpf):
        """Valida CPF usando algoritmo padrão"""
        import re
        
        # Remove caracteres não numéricos
        cpf_limpo = re.sub(r'[^0-9]', '', cpf)
        
        # Verifica se tem 11 dígitos
        if len(cpf_limpo) != 11:
            return False
        
        # Verifica se todos os dígitos são iguais
        if cpf_limpo == cpf_limpo[0] * 11:
            return False
        
        # Validação do primeiro dígito verificador
        soma = sum(int(cpf_limpo[i]) * (10 - i) for i in range(9))
        resto = soma % 11
        dv1 = 0 if resto < 2 else 11 - resto
        
        if int(cpf_limpo[9]) != dv1:
            return False
        
        # Validação do segundo dígito verificador
        soma = sum(int(cpf_limpo[i]) * (11 - i) for i in range(10))
        resto = soma % 11
        dv2 = 0 if resto < 2 else 11 - resto
        
        return int(cpf_limpo[10]) == dv2
    
    def _validar_cnpj(self, cnpj):
        """Valida CNPJ usando algoritmo padrão"""
        import re
        
        # Remove caracteres não numéricos
        cnpj_limpo = re.sub(r'[^0-9]', '', cnpj)
        
        # Verifica se tem 14 dígitos
        if len(cnpj_limpo) != 14:
            return False
        
        # Verifica se todos os dígitos são iguais
        if cnpj_limpo == cnpj_limpo[0] * 14:
            return False
        
        # Validação do primeiro dígito verificador
        sequencia = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj_limpo[i]) * sequencia[i] for i in range(12))
        resto = soma % 11
        dv1 = 0 if resto < 2 else 11 - resto
        
        if int(cnpj_limpo[12]) != dv1:
            return False
        
        # Validação do segundo dígito verificador
        sequencia = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj_limpo[i]) * sequencia[i] for i in range(13))
        resto = soma % 11
        dv2 = 0 if resto < 2 else 11 - resto
        
        return int(cnpj_limpo[13]) == dv2
    
    @property
    def contatos_principais(self):
        """Retorna lista de contatos principais da empresa"""
        contatos = []
        if self.email_principal:
            contatos.append(f"Email: {self.email_principal}")
        if self.telefone_principal:
            contatos.append(f"Tel: {self.telefone_principal}")
        return contatos
    
    @property
    def endereco_completo(self):
        """Retorna endereço formatado"""
        endereco_parts = []
        
        if self.endereco:
            endereco_parts.append(self.endereco)
            if self.numero:
                endereco_parts.append(f"nº {self.numero}")
            if self.complemento:
                endereco_parts.append(self.complemento)
        
        if self.bairro:
            endereco_parts.append(self.bairro)
        if self.cidade:
            endereco_parts.append(self.cidade)
        if self.estado:
            endereco_parts.append(self.estado)
        if self.cep:
            endereco_parts.append(f"CEP: {self.cep}")
        
        return " - ".join(endereco_parts)
    
    @property
    def nome_display(self):
        """Retorna nome para exibição (fantasia ou razão social)"""
        return self.nome_fantasia or self.razao_social


class ContatoCliente(models.Model):
    """
    Modelo para representar pessoas que trabalham na empresa cliente.
    
    Estas pessoas podem acionar o chat para obter suporte.
    Uma pessoa pode trabalhar em múltiplas empresas do mesmo grupo.
    """
    
    # Relacionamento com cliente (empresa)
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='contatos',
        verbose_name="Empresa",
        help_text="Empresa onde a pessoa trabalha"
    )
    
    # Dados da pessoa
    nome = models.CharField(
        max_length=255,
        verbose_name="Nome",
        help_text="Nome completo da pessoa"
    )
    
    cargo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Cargo",
        help_text="Cargo da pessoa na empresa"
    )
    
    # Contatos (WhatsApp é obrigatório para chat)
    whatsapp = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Formato de WhatsApp inválido. Use: +5511999999999"
            )
        ],
        verbose_name="WhatsApp",
        help_text="WhatsApp da pessoa (obrigatório para chat)"
    )
    
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="E-mail",
        help_text="E-mail da pessoa (opcional)"
    )
    
    # Status
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Se a pessoa está ativa"
    )
    
    # Auditoria
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )
    
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em"
    )
    
    criado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contatos_criados',
        verbose_name="Criado por"
    )
    
    class Meta:
        verbose_name = "Contato da Empresa"
        verbose_name_plural = "Contatos das Empresas"
        ordering = ['nome']
        indexes = [
            models.Index(fields=['cliente', 'ativo']),
            models.Index(fields=['whatsapp']),
            models.Index(fields=['nome']),
        ]
        # Uma pessoa pode ter o mesmo WhatsApp em empresas diferentes do mesmo grupo
        unique_together = [['cliente', 'whatsapp']]
    
    def __str__(self):
        return f"{self.nome} - {self.cliente.razao_social}"
    
    @property
    def contatos_disponiveis(self):
        """Retorna lista de contatos disponíveis"""
        contatos = []
        if self.whatsapp:
            contatos.append(f"WA: {self.whatsapp}")
        if self.email:
            contatos.append(f"Email: {self.email}")
        return contatos


class HistoricoCliente(models.Model):
    """
    Modelo para rastrear alterações nos dados do cliente.
    
    Mantém um histórico completo de todas as modificações.
    """
    
    # Relacionamento com cliente
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='historico',
        verbose_name="Cliente",
        help_text="Cliente que foi alterado"
    )
    
    # Dados da alteração
    campo_alterado = models.CharField(
        max_length=100,
        verbose_name="Campo Alterado",
        help_text="Nome do campo que foi alterado"
    )
    
    valor_anterior = models.TextField(
        blank=True,
        null=True,
        verbose_name="Valor Anterior",
        help_text="Valor anterior do campo"
    )
    
    valor_novo = models.TextField(
        blank=True,
        null=True,
        verbose_name="Valor Novo",
        help_text="Novo valor do campo"
    )
    
    # Metadados
    data_alteracao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data da Alteração",
        help_text="Data e hora da alteração"
    )
    
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Usuário",
        help_text="Usuário que fez a alteração"
    )
    
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações",
        help_text="Observações sobre a alteração"
    )
    
    class Meta:
        verbose_name = "Histórico do Cliente"
        verbose_name_plural = "Histórico dos Clientes"
        ordering = ['-data_alteracao']
        indexes = [
            models.Index(fields=['cliente', 'data_alteracao']),
            models.Index(fields=['campo_alterado']),
        ]
    
    def __str__(self):
        return f"{self.cliente.razao_social} - {self.campo_alterado} - {self.data_alteracao.strftime('%d/%m/%Y %H:%M')}"


class DocumentoCliente(models.Model):
    """
    Modelo para armazenar documentos anexos do cliente.
    
    Permite upload de diversos tipos de documentos.
    """
    
    # Opções para tipo de documento
    TIPO_DOCUMENTO_CHOICES = [
        ('contrato', 'Contrato'),
        ('proposta', 'Proposta'),
        ('certificado', 'Certificado'),
        ('licenca', 'Licença'),
        ('alvara', 'Alvará'),
        ('comprovante', 'Comprovante'),
        ('outro', 'Outro'),
    ]
    
    # Relacionamento com cliente
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='documentos',
        verbose_name="Cliente",
        help_text="Cliente proprietário do documento"
    )
    
    # Dados do documento
    nome = models.CharField(
        max_length=255,
        verbose_name="Nome do Documento",
        help_text="Nome descritivo do documento"
    )
    
    tipo_documento = models.CharField(
        max_length=20,
        choices=TIPO_DOCUMENTO_CHOICES,
        default='outro',
        verbose_name="Tipo de Documento",
        help_text="Tipo do documento"
    )
    
    arquivo = models.FileField(
        upload_to='clientes/documentos/',
        verbose_name="Arquivo",
        help_text="Arquivo do documento"
    )
    
    descricao = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descrição",
        help_text="Descrição do documento"
    )
    
    # Metadados
    data_upload = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data do Upload",
        help_text="Data e hora do upload"
    )
    
    usuario_upload = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Usuário do Upload",
        help_text="Usuário que fez o upload"
    )
    
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Se o documento está ativo"
    )
    
    class Meta:
        verbose_name = "Documento do Cliente"
        verbose_name_plural = "Documentos dos Clientes"
        ordering = ['-data_upload']
        indexes = [
            models.Index(fields=['cliente', 'tipo_documento']),
            models.Index(fields=['data_upload']),
        ]
    
    def __str__(self):
        return f"{self.nome} - {self.cliente.razao_social}"
    
    @property
    def tamanho_arquivo(self):
        """Retorna o tamanho do arquivo em formato legível"""
        if self.arquivo:
            size = self.arquivo.size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        return "0 B"