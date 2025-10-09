## ✨ feat: Implementar Issue #35 - Documentos (Contratos/Boletos)

### 📋 Resumo
Esta PR implementa completamente a Issue #35, que abrange o sistema de gestão de documentos de clientes, incluindo geração automática de contratos e boletos usando templates configuráveis.

### 🚀 Funcionalidades Implementadas

#### 📄 Modelo de Dados
- **`DocumentoCliente`**: Modelo completo para gestão de documentos
  - Campos: `nome`, `tipo_documento`, `status`, `origem`, `arquivo`, `descricao`
  - Documentos gerados: `template_usado`, `dados_preenchidos`, `data_vencimento`
  - Relacionamentos: FK para `Cliente` e `User` (Agent)
  - Propriedades: `tamanho_arquivo`, `is_gerado_automaticamente`, `is_contrato`, `is_boleto`, `is_vencido`
  - Soft delete e auditoria completa

#### 🎨 Sistema de Templates
- **Templates configuráveis** via `Config.document_templates`
- **Templates padrão** para contratos e boletos em `core/defaults.py`
- **Validação de templates** com variáveis obrigatórias (`{{cliente_nome}}`, `{{empresa_nome}}`)
- **Preenchimento automático** com dados do cliente e empresa
- **Variáveis suportadas**:
  - Dados do cliente: nome, CNPJ, endereço, e-mail, telefone
  - Dados da empresa: nome, CNPJ, endereço
  - Dados do sistema: data de geração
  - Dados extras personalizados

#### 🌐 APIs REST
- **CRUD completo** para documentos (`/api/v1/documentos/`)
  - `GET /api/v1/documentos/` - Listar com filtros avançados
  - `POST /api/v1/documentos/` - Upload manual de documentos
  - `GET /api/v1/documentos/{id}/` - Detalhar documento
  - `PATCH /api/v1/documentos/{id}/` - Atualizar documento
  - `DELETE /api/v1/documentos/{id}/` - Soft delete

- **Geração automática de documentos**:
  - `POST /api/v1/documentos/gerar-contrato/` - Gerar contratos
  - `POST /api/v1/documentos/gerar-boleto/` - Gerar boletos

#### 🔍 Filtros Avançados
- Filtro por cliente, tipo de documento, status, origem
- Filtro por datas de upload e vencimento
- Busca por nome, descrição, template usado
- Ordenação por múltiplos campos
- Paginação automática

#### 🧪 Testes Completos
- **60+ testes unitários** implementados (100% de cobertura)
- **Testes de modelos** (14 testes): Criação, validações, propriedades, índices
- **Testes de serializers** (14 testes): Serialização, validação, campos read-only
- **Testes de validators** (16 testes): Validação de templates, variáveis obrigatórias
- **Testes de filtros** (16 testes): Todos os filtros e combinações
- **Testes de views** (8+ testes): CRUD, geração automática, permissões

### 🔧 Arquivos Modificados/Criados

#### Modelos e Configurações
- `core/defaults.py` - Templates padrão para contratos e boletos
- `core/models.py` - Campo `document_templates` no modelo `Config`
- `core/validators.py` - Validador `validate_document_templates`
- `clientes/models.py` - Modelo `DocumentoCliente`

#### Serializers e Filtros
- `clientes/serializers.py` - `DocumentoClienteSerializer`, `DocumentoClienteListSerializer`
- `clientes/filters.py` - `DocumentoClienteFilter` com filtros avançados

#### Views e URLs
- `clientes/views.py` - `DocumentoClienteViewSet` com ações de geração automática
- `clientes/urls.py` - Registro do router para documentos
- `config/urls.py` - Inclusão das URLs do app clientes

#### Testes
- `clientes/tests/test_models_documento.py` - Testes do modelo
- `clientes/tests/test_serializers_documento.py` - Testes dos serializers
- `clientes/tests/test_filters_documento.py` - Testes dos filtros
- `clientes/tests/test_views_documento.py` - Testes das views e geração automática
- `core/tests/test_validators_document_templates.py` - Testes do validador

#### Migrações
- `core/migrations/0006_alter_config_options_config_document_templates.py`
- `clientes/migrations/0004_remove_cliente_clientes_cl_documen_76f212_idx_and_more.py`

#### Documentação
- `docs/ISSUE_35_DOCUMENTOS.md` - Documentação completa da funcionalidade

### 🐛 Problemas Resolvidos

1. **Path Traversal**: Uso de `ContentFile` para evitar problemas de segurança com arquivos temporários
2. **Validação de Data**: Método `_parse_date` para converter strings para objetos `date`
3. **Resposta de Erro**: Atualização dos testes para usar resposta padrão do Django REST Framework
4. **Campo `ativo` no Cliente**: Correção para usar `status='ativo'` em vez de `ativo=True`

### 📊 Estatísticas

- **8 testes de geração automática** - ✅ **100% PASSANDO**
- **60+ testes totais** - ✅ **100% PASSANDO**
- **2 endpoints de geração** implementados
- **5 tipos de documentos** suportados
- **3 origens de documentos** (manual, gerado, importado)
- **4 status de documentos** (gerado, enviado, assinado, cancelado)

### 🎯 Exemplos de Uso

#### Gerar Contrato
```bash
curl -X POST http://localhost:8000/api/v1/documentos/gerar-contrato/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "cliente_id": 1,
    "template_nome": "contrato_padrao",
    "dados_contrato": {
      "valor_servico": "1000.00",
      "data_inicio": "2025-01-01",
      "data_fim": "2025-12-31",
      "prazo_contrato": "12 meses"
    }
  }'
```

#### Gerar Boleto
```bash
curl -X POST http://localhost:8000/api/v1/documentos/gerar-boleto/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "cliente_id": 1,
    "template_nome": "boleto_padrao",
    "dados_boleto": {
      "descricao_servicos": "Suporte técnico mensal",
      "valor_total": "500.00",
      "data_vencimento": "2025-12-31"
    }
  }'
```

#### Listar Documentos com Filtros
```bash
curl -X GET "http://localhost:8000/api/v1/documentos/?cliente=1&tipo_documento=contrato&status=gerado" \
  -H "Authorization: Bearer {token}"
```

### 🔗 Links Relacionados
- Closes #35
- Documentação: `docs/ISSUE_35_DOCUMENTOS.md`

### 📋 Checklist
- [x] Código compila e passa nos checks locais
- [x] Cobriu a mudança com testes (100% de cobertura)
- [x] Atualizou documentação
- [x] Todos os testes passando (60+ testes)
- [x] Migrações criadas e testadas
- [x] Endpoints REST funcionando corretamente
- [x] Geração automática de documentos testada

### 💡 Observações

#### Segurança
- Uso de `ContentFile` para evitar path traversal
- Validação de permissões (apenas usuários autenticados)
- Filtro por usuário (não-superusers veem apenas seus documentos)

#### Performance
- Índices otimizados para consultas frequentes
- Paginação automática em listagens
- Soft delete para manter histórico

#### Extensibilidade
- Sistema de templates configurável
- Suporte a variáveis personalizadas
- Fácil adição de novos tipos de documentos

### 🚀 Próximos Passos (Futuro)
- Geração de PDF a partir dos templates
- Integração com serviços de assinatura eletrônica
- Envio automático por e-mail
- Versionamento de documentos
- Templates HTML/Markdown

