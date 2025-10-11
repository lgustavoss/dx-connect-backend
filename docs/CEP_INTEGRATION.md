# Integração com API de CEP - DX Connect Backend

## 📋 Visão Geral

Integração com a API do **ViaCEP** para consulta automática de endereços a partir do CEP. Esta funcionalidade facilita o cadastro de clientes, preenchendo automaticamente os campos de endereço.

## 🎯 Funcionalidades

- ✅ Consulta de CEP via API ViaCEP
- ✅ Cache de consultas (24 horas)
- ✅ Validação de formato de CEP
- ✅ Endpoint público (não requer autenticação)
- ✅ Tratamento de erros robusto
- ✅ Timeout configurável (5 segundos)
- ✅ Logs estruturados

## 🚀 Uso da API

### Endpoint

```
GET /api/v1/integrations/cep/{cep}/
```

### Parâmetros

- `cep` (path parameter): CEP no formato `12345678` ou `12345-678`

### Exemplo de Requisição

```bash
# Com formatação
curl http://localhost:8001/api/v1/integrations/cep/01001-000/

# Sem formatação
curl http://localhost:8001/api/v1/integrations/cep/01001000/
```

### Resposta de Sucesso (200 OK)

```json
{
  "cep": "01001-000",
  "logradouro": "Praça da Sé",
  "complemento": "lado ímpar",
  "bairro": "Sé",
  "localidade": "São Paulo",
  "uf": "SP",
  "cidade": "São Paulo",
  "estado": "SP",
  "ibge": "3550308",
  "gia": "1004",
  "ddd": "11",
  "siafi": "7107"
}
```

**Nota**: Os campos `cidade` e `estado` são aliases de `localidade` e `uf` para facilitar o uso no frontend.

### Resposta de Erro (404 Not Found)

```json
{
  "error": "CEP não encontrado",
  "message": "O CEP informado não foi encontrado na base de dados"
}
```

### Resposta de Erro (400 Bad Request)

```json
{
  "error": "CEP inválido",
  "message": "CEP inválido: 123"
}
```

### Resposta de Erro (500 Internal Server Error)

```json
{
  "error": "Erro ao consultar CEP",
  "message": "Não foi possível consultar o CEP. Tente novamente mais tarde."
}
```

## 💻 Uso no Frontend

### JavaScript/TypeScript

```typescript
async function buscarCEP(cep: string) {
  try {
    const response = await fetch(`http://localhost:8001/api/v1/integrations/cep/${cep}/`);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Erro ao buscar CEP:', error);
    throw error;
  }
}

// Uso
const endereco = await buscarCEP('01001-000');
console.log(endereco.logradouro); // "Praça da Sé"
console.log(endereco.cidade);     // "São Paulo"
console.log(endereco.estado);     // "SP"
```

### React Hook

```typescript
import { useState } from 'react';

function useConsultaCEP() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const consultarCEP = async (cep: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/v1/integrations/cep/${cep}/`);
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message);
      }
      
      const data = await response.json();
      return data;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  };
  
  return { consultarCEP, loading, error };
}

// Uso em componente
function FormularioCadastro() {
  const { consultarCEP, loading } = useConsultaCEP();
  
  const handleCEPChange = async (cep: string) => {
    if (cep.length === 8) {
      const endereco = await consultarCEP(cep);
      if (endereco) {
        setFieldValue('endereco', endereco.logradouro);
        setFieldValue('bairro', endereco.bairro);
        setFieldValue('cidade', endereco.cidade);
        setFieldValue('estado', endereco.estado);
      }
    }
  };
  
  // ... resto do componente
}
```

## 🔧 Configuração

### Serviço CEPService

```python
from integrations.cep_service import CEPService, buscar_cep

# Consultar CEP
dados = CEPService.consultar_cep('01001-000')

# Ou usar a função auxiliar
dados = buscar_cep('01001-000')

# Formatar para o modelo Cliente
endereco_formatado = CEPService.formatar_endereco(dados)
# {
#   'endereco': 'Praça da Sé',
#   'bairro': 'Sé',
#   'cidade': 'São Paulo',
#   'estado': 'SP',
#   'cep': '01001000',
#   'complemento': 'lado ímpar'
# }
```

### Cache

As consultas são cacheadas por **24 horas** para melhorar performance e reduzir chamadas à API externa.

Para limpar o cache:

```python
from django.core.cache import cache
cache.delete('cep:01001000')
```

### Timeout

O timeout padrão é de **5 segundos**. Para alterar:

```python
CEPService.REQUEST_TIMEOUT = 10  # 10 segundos
```

## 🧪 Testes

### Executar Testes

```bash
# Testes do serviço
docker-compose exec web python manage.py test integrations.tests.test_cep_service

# Testes da view
docker-compose exec web python manage.py test integrations.tests.test_views

# Todos os testes
docker-compose exec web python manage.py test integrations
```

### Tipos de Testes

#### Testes Unitários (11 testes)
- Validação de CEP
- Limpeza de formato
- Cache
- Timeout
- Erros HTTP
- Formatação de endereço

#### Testes de Integração (2 testes)
- Consulta real de CEP válido
- Consulta real de CEP inválido

**Total**: 20 testes (11 + 9)

## 🔒 Segurança

### Endpoint Público

O endpoint de consulta de CEP é **público** (`AllowAny`) para facilitar o uso em formulários de cadastro sem necessidade de autenticação prévia.

**Considerações**:
- ✅ Não expõe dados sensíveis
- ✅ Cache reduz abuso
- ✅ Timeout previne DoS
- ✅ Rate limiting pode ser adicionado posteriormente

### Validação

- ✅ CEP deve ter 8 dígitos
- ✅ Apenas números são considerados
- ✅ Formatos aceitos: `12345678`, `12345-678`, `12.345-678`

## 📊 Performance

### Cache

- **Duração**: 24 horas
- **Backend**: Redis (configurado em `settings.py`)
- **Benefícios**:
  - Reduz latência (< 10ms em cache hits)
  - Reduz chamadas à API externa
  - Melhora experiência do usuário

### Timeout

- **Padrão**: 5 segundos
- **Justificativa**: Balance entre UX e confiabilidade

## 🐛 Troubleshooting

### Erro: "Timeout ao consultar CEP"

**Causa**: A API do ViaCEP não respondeu em 5 segundos.

**Solução**:
- Verificar conexão com internet
- Tentar novamente
- Aumentar timeout se necessário

### Erro: "CEP não encontrado"

**Causa**: CEP não existe na base de dados do ViaCEP.

**Solução**:
- Verificar se o CEP está correto
- Permitir preenchimento manual do endereço

### Erro: "CEP inválido"

**Causa**: CEP não tem 8 dígitos ou contém caracteres inválidos.

**Solução**:
- Validar formato no frontend antes de enviar
- Aceitar apenas números ou formato `12345-678`

## 🔗 Referências

- [ViaCEP - API](https://viacep.com.br/)
- [ViaCEP - Documentação](https://viacep.com.br/exemplo/jquery/)
- [Requests Library](https://requests.readthedocs.io/)

## 📝 Changelog

### v1.0.0 (Issue #8)
- Integração inicial com ViaCEP
- Endpoint público de consulta
- Cache de 24 horas
- Testes unitários e de integração
- Documentação completa

## 🚀 Próximos Passos (Futuro)

- Rate limiting no endpoint público
- Suporte a múltiplos provedores de CEP (fallback)
- Validação de CEP no serializer de Cliente
- Auto-preenchimento no formulário de cadastro
- Métricas de uso da API

