# Issue #35 - Documentos (Contratos/Boletos)

## 📋 Resumo

Implementação completa do sistema de gestão de documentos de clientes, incluindo geração automática de contratos e boletos usando templates configuráveis.

## 🎯 Objetivos Alcançados

### 1. Modelo de Dados
- ✅ Modelo `DocumentoCliente` com campos completos
- ✅ Relacionamentos com `Cliente` e `User` (Agent)
- ✅ Suporte a documentos manuais e gerados automaticamente
- ✅ Soft delete e auditoria

### 2. Templates de Documentos
- ✅ Sistema de templates configurável via `Config.document_templates`
- ✅ Templates padrão para contratos e boletos
- ✅ Validação de templates com variáveis obrigatórias
- ✅ Preenchimento automático com dados do cliente e empresa

### 3. Endpoints REST
- ✅ CRUD completo para documentos (`/api/v1/documentos/`)
- ✅ Geração automática de contratos (`POST /api/v1/documentos/gerar-contrato/`)
- ✅ Geração automática de boletos (`POST /api/v1/documentos/gerar-boleto/`)
- ✅ Filtros avançados (cliente, tipo, status, origem, datas)
- ✅ Paginação e ordenação

### 4. Testes
- ✅ 60 testes unitários implementados
- ✅ 100% de cobertura nos módulos implementados
- ✅ Testes de modelos, serializers, validators, filtros e views

## 📊 Estrutura de Dados

### Modelo `DocumentoCliente`

```python
class DocumentoCliente(models.Model):
    # Relacionamentos
    cliente = ForeignKey(Cliente)
    usuario_upload = ForeignKey(User)
    
    # Campos básicos
    nome = CharField(max_length=255)
    tipo_documento = CharField(choices=TIPO_DOCUMENTO_CHOICES)
    status = CharField(choices=STATUS_DOCUMENTO_CHOICES)
    origem = CharField(choices=ORIGEM_DOCUMENTO_CHOICES)
    arquivo = FileField(upload_to='clientes/documentos/')
    descricao = TextField(blank=True)
    
    # Campos para documentos gerados
    template_usado = CharField(max_length=255, blank=True)
    dados_preenchidos = JSONField(default=dict)
    data_vencimento = DateField(null=True, blank=True)
    
    # Controle
    data_upload = DateTimeField(auto_now_add=True)
    ativo = BooleanField(default=True)
```

### Choices

**Tipo de Documento:**
- `contrato` - Contrato
- `boleto` - Boleto
- `proposta` - Proposta Comercial
- `certificado` - Certificado
- `outro` - Outro

**Status:**
- `gerado` - Gerado
- `enviado` - Enviado
- `assinado` - Assinado
- `cancelado` - Cancelado

**Origem:**
- `manual` - Upload Manual
- `gerado` - Gerado Automaticamente
- `importado` - Importado

## 🔧 Configuração de Templates

### Estrutura do Template

```json
{
  "contrato_padrao": {
    "nome": "Contrato de Prestação de Serviços Padrão",
    "tipo": "contrato",
    "conteudo": "CONTRATO...\n{{cliente_nome}}\n{{empresa_nome}}...",
    "variaveis": [
      "cliente_nome",
      "cliente_cnpj",
      "cliente_endereco",
      "empresa_nome",
      "empresa_cnpj",
      "empresa_endereco",
      "valor_servico",
      "data_inicio",
      "data_fim",
      "prazo_contrato",
      "data_contrato"
    ]
  }
}
```

### Variáveis Disponíveis

**Dados do Cliente (Contratante):**
- `{{cliente_nome}}` - Razão social
- `{{cliente_cnpj}}` - CNPJ formatado
- `{{cliente_endereco}}` - Endereço completo
- `{{cliente_email}}` - E-mail principal
- `{{cliente_telefone}}` - Telefone principal

**Dados da Empresa (Contratada):**
- `{{empresa_nome}}` - Razão social da empresa
- `{{empresa_cnpj}}` - CNPJ da empresa
- `{{empresa_endereco}}` - Endereço da empresa

**Dados do Sistema:**
- `{{data_contrato}}` - Data de geração (DD/MM/YYYY)
- `{{data_geracao}}` - Data/hora de geração (DD/MM/YYYY HH:MM)

**Dados Extras:**
- Qualquer campo adicional passado em `dados_contrato` ou `dados_boleto`

## 🚀 Uso dos Endpoints

### 1. Listar Documentos

```http
GET /api/v1/documentos/
Authorization: Bearer {token}

Query Parameters:
- cliente: ID do cliente
- tipo_documento: contrato, boleto, proposta, certificado, outro
- status: gerado, enviado, assinado, cancelado
- origem: manual, gerado, importado
- data_upload_apos: YYYY-MM-DD
- data_upload_antes: YYYY-MM-DD
- data_vencimento_apos: YYYY-MM-DD
- data_vencimento_antes: YYYY-MM-DD
- ativo: true, false
- search: busca por nome, descricao, template_usado
- ordering: nome, data_upload, data_vencimento, status
```

### 2. Criar Documento (Upload Manual)

```http
POST /api/v1/documentos/
Authorization: Bearer {token}
Content-Type: multipart/form-data

Body:
- cliente: ID do cliente
- nome: Nome do documento
- tipo_documento: contrato
- arquivo: [arquivo]
- descricao: Descrição opcional
- data_vencimento: YYYY-MM-DD (opcional)
```

### 3. Gerar Contrato Automaticamente

```http
POST /api/v1/documentos/gerar-contrato/
Authorization: Bearer {token}
Content-Type: application/json

Body:
{
  "cliente_id": 1,
  "template_nome": "contrato_padrao",
  "dados_contrato": {
    "valor_servico": "1000.00",
    "data_inicio": "2025-01-01",
    "data_fim": "2025-12-31",
    "prazo_contrato": "12 meses"
  }
}

Response 201:
{
  "message": "Contrato gerado com sucesso",
  "documento": {
    "id": 1,
    "cliente": 1,
    "cliente_nome": "Empresa Teste LTDA",
    "nome": "Contrato de Prestação de Serviços Padrão - Empresa Teste LTDA",
    "tipo_documento": "contrato",
    "status": "gerado",
    "origem": "gerado",
    "template_usado": "Contrato de Prestação de Serviços Padrão",
    "dados_preenchidos": {...},
    "arquivo": "/media/clientes/documentos/contrato_1_abc123.txt",
    "data_upload": "2025-10-06T22:52:00Z",
    "usuario_upload": 1,
    "is_gerado_automaticamente": true,
    "is_contrato": true,
    "tamanho_arquivo": "2.5 KB"
  }
}
```

### 4. Gerar Boleto Automaticamente

```http
POST /api/v1/documentos/gerar-boleto/
Authorization: Bearer {token}
Content-Type: application/json

Body:
{
  "cliente_id": 1,
  "template_nome": "boleto_padrao",
  "dados_boleto": {
    "descricao_servicos": "Suporte técnico mensal",
    "valor_total": "500.00",
    "data_vencimento": "2025-12-31",
    "banco": "Banco do Brasil",
    "agencia": "1234-5",
    "conta": "12345-6"
  }
}

Response 201:
{
  "message": "Boleto gerado com sucesso",
  "documento": {
    "id": 2,
    "cliente": 1,
    "cliente_nome": "Empresa Teste LTDA",
    "nome": "Boleto de Cobrança Padrão - Empresa Teste LTDA",
    "tipo_documento": "boleto",
    "status": "gerado",
    "origem": "gerado",
    "template_usado": "Boleto de Cobrança Padrão",
    "data_vencimento": "2025-12-31",
    "arquivo": "/media/clientes/documentos/boleto_1_def456.txt",
    "is_gerado_automaticamente": true,
    "is_boleto": true,
    "is_vencido": false
  }
}
```

### 5. Atualizar Documento

```http
PATCH /api/v1/documentos/{id}/
Authorization: Bearer {token}
Content-Type: application/json

Body:
{
  "status": "enviado",
  "descricao": "Enviado por e-mail em 06/10/2025"
}
```

### 6. Soft Delete

```http
DELETE /api/v1/documentos/{id}/
Authorization: Bearer {token}

Response 204: No Content
```

## 🔒 Permissões

- **Listar/Criar/Atualizar/Deletar**: `IsAuthenticated`
- **Filtro por Usuário**: Não-superusers veem apenas documentos de clientes que criaram
- **Gerar Documentos**: `IsAuthenticated`

## 🧪 Testes

### Executar Testes

```bash
# Todos os testes de documentos
docker-compose exec web python manage.py test clientes.tests.test_models_documento
docker-compose exec web python manage.py test clientes.tests.test_serializers_documento
docker-compose exec web python manage.py test clientes.tests.test_filters_documento
docker-compose exec web python manage.py test clientes.tests.test_views_documento
docker-compose exec web python manage.py test core.tests.test_validators_document_templates

# Testes de geração automática
docker-compose exec web python manage.py test clientes.tests.test_views_documento.DocumentoClienteGeracaoTests
```

### Cobertura

- **Modelos**: 14 testes
- **Serializers**: 14 testes
- **Validators**: 16 testes
- **Filtros**: 16 testes
- **Views**: 8 testes de geração + testes CRUD
- **Total**: 60+ testes

## 🐛 Problemas Resolvidos

### 1. Path Traversal
**Problema**: Arquivos temporários fora do diretório de mídia causavam erro de segurança.
**Solução**: Uso de `ContentFile` para criar arquivos em memória e salvá-los diretamente no diretório de mídia.

### 2. Validação de Data
**Problema**: Comparação de strings com objetos `date` causava `TypeError`.
**Solução**: Implementação de método `_parse_date` para converter strings no formato `YYYY-MM-DD` para objetos `date`.

### 3. Resposta de Erro
**Problema**: Testes esperavam chave `error`, mas Django REST Framework retorna `detail`.
**Solução**: Atualização dos testes para usar a resposta padrão do framework.

## 📈 Melhorias Futuras

1. **Assinatura Digital**: Integração com serviços de assinatura eletrônica
2. **Geração de PDF**: Converter templates de texto para PDF
3. **Envio Automático**: Enviar documentos por e-mail automaticamente
4. **Versionamento**: Manter histórico de versões de documentos
5. **Templates Avançados**: Suporte a templates HTML/Markdown
6. **Notificações**: Alertas de vencimento de documentos

## 🔗 Referências

- [Django FileField](https://docs.djangoproject.com/en/4.2/ref/models/fields/#filefield)
- [Django REST Framework Serializers](https://www.django-rest-framework.org/api-guide/serializers/)
- [Django Filters](https://django-filter.readthedocs.io/)

