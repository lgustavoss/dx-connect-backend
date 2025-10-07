DEFAULT_COMPANY_DATA = {
    "razao_social": "",
    "nome_fantasia": "",
    "cnpj": "",
    "inscricao_estadual": "",
    "inscricao_municipal": "",
    "regime_tributario": "1",
    "cnae_principal": "",
    "telefone": "",
    "email": "",
    "site": "",
    "endereco": {
        "cep": "01234567",
        "logradouro": "",
        "numero": "",
        "complemento": "",
        "bairro": "",
        "cidade": "",
        "uf": "SP",
    },
}

DEFAULT_CHAT_SETTINGS = {
    "mensagem_saudacao": "Olá! Como podemos ajudar?",
    "mensagem_fora_expediente": "Estamos fora do horário de atendimento.",
    "mensagem_encerramento": "Obrigado pelo contato!",
    "mensagem_inatividade": "Estamos encerrando por inatividade.",
    "timeout_inatividade_minutos": 15,
    "limite_chats_simultaneos": 5,
    "horario_funcionamento": {
        "segunda": {"inicio": "08:00", "fim": "18:00"},
        "terca": {"inicio": "08:00", "fim": "18:00"},
        "quarta": {"inicio": "08:00", "fim": "18:00"},
        "quinta": {"inicio": "08:00", "fim": "18:00"},
        "sexta": {"inicio": "08:00", "fim": "18:00"},
        "sabado": {"inicio": None, "fim": None},
        "domingo": {"inicio": None, "fim": None},
    },
}

DEFAULT_EMAIL_SETTINGS = {
    "smtp_host": "",
    "smtp_port": 587,
    "smtp_usuario": "",
    "smtp_senha": "",
    "smtp_ssl": True,
    "email_from": "",
}

DEFAULT_APPEARANCE_SETTINGS = {
    "login_logo_url": "",
    "favicon_url": "",
    "primary_color": "#0ea5e9",
    "secondary_color": "#111827",
    "custom_css": "",
}

# WhatsApp: valores padrão (não sensíveis)
DEFAULT_WHATSAPP_SETTINGS = {
    "enabled": False,
    "device_name": "DXConnect",
    "stealth_mode": True,
    "human_delays": True,
    "reconnect_backoff_seconds": 5,
    # Segredos/artefatos sensíveis (armazenados criptografados quando presentes)
    "session_data": "",
    "proxy_url": "",
}

DEFAULT_DOCUMENT_TEMPLATES = {
    "contrato_padrao": {
        "nome": "Contrato de Prestação de Serviços Padrão",
        "tipo": "contrato",
        "conteudo": """
CONTRATO DE PRESTAÇÃO DE SERVIÇOS

CONTRATANTE: {{cliente_nome}}
CNPJ: {{cliente_cnpj}}
Endereço: {{cliente_endereco}}

CONTRATADA: {{empresa_nome}}
CNPJ: {{empresa_cnpj}}
Endereço: {{empresa_endereco}}

OBJETO: Prestação de serviços de suporte técnico conforme especificado.

VALOR: R$ {{valor_servico}}
VIGÊNCIA: {{data_inicio}} a {{data_fim}}

Cláusulas:
1. O contratante se compromete ao pagamento dos serviços.
2. A contratada prestará suporte técnico conforme acordado.
3. Este contrato tem vigência de {{prazo_contrato}}.

{{data_contrato}}

________________________        ________________________
    CONTRATANTE                       CONTRATADA
""",
        "variaveis": [
            "cliente_nome", "cliente_cnpj", "cliente_endereco",
            "empresa_nome", "empresa_cnpj", "empresa_endereco",
            "valor_servico", "data_inicio", "data_fim", "prazo_contrato", "data_contrato"
        ]
    },
    "boleto_padrao": {
        "nome": "Boleto de Cobrança Padrão",
        "tipo": "boleto",
        "conteudo": """
BOLETO DE COBRANÇA

Cliente: {{cliente_nome}}
CNPJ: {{cliente_cnpj}}

Serviços: {{descricao_servicos}}
Valor: R$ {{valor_total}}
Vencimento: {{data_vencimento}}

Empresa: {{empresa_nome}}
CNPJ: {{empresa_cnpj}}
Banco: {{banco}}
Agência: {{agencia}}
Conta: {{conta}}
""",
        "variaveis": [
            "cliente_nome", "cliente_cnpj", "descricao_servicos",
            "valor_total", "data_vencimento", "empresa_nome",
            "empresa_cnpj", "banco", "agencia", "conta"
        ]
    }
}