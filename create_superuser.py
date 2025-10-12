"""
Script para criar superusuário no DX Connect.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Verificar se já existe superuser
existing_superusers = User.objects.filter(is_superuser=True)

if existing_superusers.exists():
    print("\n" + "="*60)
    print("SUPERUSUÁRIOS EXISTENTES:")
    print("="*60)
    for user in existing_superusers:
        print(f"\nID: {user.id}")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Display Name: {user.display_name}")
        print(f"Ativo: {'Sim' if user.is_active else 'Não'}")
        print(f"Criado em: {user.date_joined}")
    print("\n" + "="*60)
else:
    print("\n" + "="*60)
    print("NENHUM SUPERUSUÁRIO ENCONTRADO!")
    print("="*60)
    print("\nCriando superusuário padrão...\n")
    
    # Criar superusuário padrão
    user = User.objects.create_superuser(
        username='admin',
        email='admin@dxconnect.com',
        password='admin123',
        display_name='Administrador',
        phone_number=''
    )
    
    print("✅ SUPERUSUÁRIO CRIADO COM SUCESSO!")
    print("="*60)
    print(f"\nUsername: {user.username}")
    print(f"Email: {user.email}")
    print(f"Senha: admin123")
    print(f"Display Name: {user.display_name}")
    print("\n" + "="*60)
    print("\n📝 CREDENCIAIS PARA LOGIN NA API:")
    print("="*60)
    print('\nPOST /api/v1/auth/token/')
    print('Content-Type: application/json\n')
    print('{')
    print('  "username": "admin",')
    print('  "password": "admin123"')
    print('}\n')
    print("="*60)
    print("\n🌐 Teste no navegador:")
    print("http://localhost:8001/api/docs/")
    print("\n✅ Pronto para uso!")
    print("="*60 + "\n")

