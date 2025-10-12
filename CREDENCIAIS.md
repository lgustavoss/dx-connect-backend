# 🔐 Credenciais de Acesso - DX Connect Backend

## ✅ **Superusuário Criado**

### 📝 **Credenciais:**
- **Username**: `admin`
- **Password**: `admin123`
- **Email**: `admin@dxconnect.com`
- **Display Name**: Administrador

---

## 🧪 **Como Testar**

### **1. Via Swagger UI (Recomendado)**

Acesse: http://localhost:8001/api/docs/

1. Clique em **"POST /api/v1/auth/token/"**
2. Clique em **"Try it out"**
3. Cole no corpo:
```json
{
  "username": "admin",
  "password": "admin123"
}
```
4. Clique em **"Execute"**
5. Copie o `access` token da resposta
6. Clique em **"Authorize"** (cadeado no topo)
7. Cole: `Bearer {seu_token}`
8. Agora pode testar todos os endpoints!

---

### **2. Via Postman/Insomnia**

**Login:**
```
POST http://localhost:8001/api/v1/auth/token/
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**Resposta:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Usar em outras requests:**
```
GET http://localhost:8001/api/v1/me/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

### **3. Via JavaScript (Frontend)**

```javascript
// Login
const response = await fetch('http://localhost:8001/api/v1/auth/token/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'admin',
    password: 'admin123'
  })
});

const data = await response.json();
console.log('Token:', data.access);

// Usar token
const meResponse = await fetch('http://localhost:8001/api/v1/me/', {
  headers: {
    'Authorization': `Bearer ${data.access}`
  }
});

const userData = await meResponse.json();
console.log('Meus dados:', userData);
```

---

### **4. Via Admin Django**

Acesse: http://localhost:8001/admin/

- **Username**: `admin`
- **Password**: `admin123`

---

## 🔄 **Criar Mais Usuários (Atendentes)**

### Via Admin Django:
1. Acesse http://localhost:8001/admin/
2. Faça login com `admin / admin123`
3. Vá em **Accounts > Agents**
4. Clique em **"Add Agent"**
5. Preencha os dados
6. **Importante**: Marque "Active" e defina grupos/permissões

### Via Django Shell:
```bash
docker-compose exec web python manage.py shell
```

```python
from django.contrib.auth import get_user_model
User = get_user_model()

# Criar atendente
atendente = User.objects.create_user(
    username='joao',
    email='joao@dxconnect.com',
    password='senha123',
    display_name='João Silva',
    phone_number='11999999999',
    is_staff=True,  # Para acessar admin
    is_active=True
)

print(f"✅ Atendente criado: {atendente.username}")
```

---

## 🔒 **Trocar Senha do Admin**

### Via Django Shell:
```python
from django.contrib.auth import get_user_model
User = get_user_model()

admin = User.objects.get(username='admin')
admin.set_password('nova_senha_forte')
admin.save()

print("✅ Senha alterada com sucesso!")
```

---

## 📊 **Verificar Todos os Usuários**

```bash
docker-compose exec web python manage.py shell
```

```python
from django.contrib.auth import get_user_model
User = get_user_model()

print("\n=== TODOS OS USUÁRIOS ===\n")
for user in User.objects.all():
    print(f"ID: {user.id}")
    print(f"Username: {user.username}")
    print(f"Email: {user.email}")
    print(f"Superuser: {'Sim' if user.is_superuser else 'Não'}")
    print(f"Staff: {'Sim' if user.is_staff else 'Não'}")
    print(f"Ativo: {'Sim' if user.is_active else 'Não'}")
    print("-" * 40)
```

---

## ⚠️ **IMPORTANTE - PRODUÇÃO**

**Nunca use credenciais fracas em produção!**

Para produção:
- Username único e seguro
- Senha forte (mínimo 12 caracteres, letras, números, símbolos)
- Email real
- Ativar 2FA se possível

---

## 🎯 **Script Rápido de Verificação**

Criei o arquivo `create_superuser.py` na raiz do projeto.

**Para verificar/criar:**
```bash
docker-compose exec web python create_superuser.py
```

**Se já existir**, mostra os dados.  
**Se não existir**, cria automaticamente com:
- Username: `admin`
- Password: `admin123`
- Email: `admin@dxconnect.com`

---

## ✅ **Resumo das Credenciais Atuais**

```
Username: admin
Password: admin123
Email: admin@dxconnect.com

API Login: POST /api/v1/auth/token/
Admin Panel: http://localhost:8001/admin/
Swagger UI: http://localhost:8001/api/docs/
```

**Pronto para usar!** 🚀

