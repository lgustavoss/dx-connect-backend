#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('/app')
django.setup()

from clientes.models import Cliente, GrupoEmpresa, DocumentoCliente
from django.contrib.auth import get_user_model
from core.models import Config
from core.defaults import DEFAULT_DOCUMENT_TEMPLATES
import tempfile

User = get_user_model()

# Criar dados de teste
user = User.objects.create_user(username='testuser4', password='testpass123')
grupo = GrupoEmpresa.objects.create(nome='Grupo Teste 4')
cliente = Cliente.objects.create(
    razao_social='Empresa Teste LTDA',
    cnpj='11.222.333/0001-84',
    grupo_empresa=grupo,
    responsavel_legal_nome='João Silva',
    responsavel_legal_cpf='111.111.111-14',
    criado_por=user,
    email_principal='contato@empresateste.com',
    telefone_principal='(11) 99999-9999',
    endereco='Rua das Flores, 123, Centro, São Paulo - SP, 01234-567',
    numero='123',
    bairro='Centro',
    cidade='São Paulo',
    estado='SP',
    cep='01234-567'
)

# Testar criação de documento
template = DEFAULT_DOCUMENT_TEMPLATES.get('contrato_padrao')
dados_extra = {'valor_servico': '1000.00', 'prazo_contrato': '12 meses'}

try:
    # Simular o que o método _gerar_documento_automatico faz
    config = Config.objects.first()
    empresa_data = config.company_data if config else {}
    
    dados_preenchimento = {
        'cliente_nome': cliente.razao_social,
        'cliente_cnpj': cliente.cnpj,
        'cliente_endereco': cliente.endereco_completo,
        'cliente_email': cliente.email_principal,
        'cliente_telefone': cliente.telefone_principal,
        'empresa_nome': empresa_data.get('razao_social', 'Empresa'),
        'empresa_cnpj': empresa_data.get('cnpj', ''),
        'empresa_endereco': f"{empresa_data.get('endereco', {}).get('logradouro', '')}, {empresa_data.get('endereco', {}).get('numero', '')} - {empresa_data.get('endereco', {}).get('bairro', '')}",
        **dados_extra,
        'data_contrato': '06/10/2025',
        'data_geracao': '06/10/2025 22:42',
    }
    
    print('Dados de preenchimento criados com sucesso')
    
    # Preencher template
    conteudo_preenchido = template['conteudo']
    for variavel, valor in dados_preenchimento.items():
        conteudo_preenchido = conteudo_preenchido.replace(f'{{{{{variavel}}}}}', str(valor))
    
    print('Template preenchido com sucesso')
    
    # Criar arquivo temporário
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(conteudo_preenchido)
        arquivo_temp = f.name
    
    print('Arquivo temporário criado:', arquivo_temp)
    
    # Criar documento no banco
    documento = DocumentoCliente.objects.create(
        cliente=cliente,
        nome=f"{template['nome']} - {cliente.razao_social}",
        tipo_documento='contrato',
        status='gerado',
        origem='gerado',
        template_usado=template['nome'],
        dados_preenchidos=dados_preenchimento,
        data_vencimento=None,
        usuario_upload=user,
        arquivo=arquivo_temp
    )
    
    print('Documento criado com sucesso:', documento.id, documento.nome)
    
    # Limpar arquivo temporário
    try:
        os.unlink(arquivo_temp)
        print('Arquivo temporário removido')
    except:
        print('Erro ao remover arquivo temporário')
        
except Exception as e:
    print('Erro:', e)
    import traceback
    traceback.print_exc()
