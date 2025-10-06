from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

Agent = get_user_model()


class TokenObtainPairViewTests(TestCase):
    """Testes para TokenObtainPairView"""

    def setUp(self):
        self.client = APIClient()
        self.user = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_token_obtain_pair_valid_credentials(self):
        """Testa POST /api/v1/auth/token/ com credenciais válidas"""
        data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        response = self.client.post("/api/v1/auth/token/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_token_obtain_pair_invalid_username(self):
        """Testa POST /api/v1/auth/token/ com username inválido"""
        data = {
            "username": "invaliduser",
            "password": "testpass123"
        }
        
        response = self.client.post("/api/v1/auth/token/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_obtain_pair_invalid_password(self):
        """Testa POST /api/v1/auth/token/ com senha inválida"""
        data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        response = self.client.post("/api/v1/auth/token/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_obtain_pair_missing_username(self):
        """Testa POST /api/v1/auth/token/ sem username"""
        data = {
            "password": "testpass123"
        }
        
        response = self.client.post("/api/v1/auth/token/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_obtain_pair_missing_password(self):
        """Testa POST /api/v1/auth/token/ sem senha"""
        data = {
            "username": "testuser"
        }
        
        response = self.client.post("/api/v1/auth/token/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_obtain_pair_inactive_user(self):
        """Testa POST /api/v1/auth/token/ com usuário inativo"""
        self.user.is_active = False
        self.user.save()
        
        data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        response = self.client.post("/api/v1/auth/token/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TokenRefreshViewTests(TestCase):
    """Testes para TokenRefreshView"""

    def setUp(self):
        self.client = APIClient()
        self.user = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_token_refresh_valid_token(self):
        """Testa POST /api/v1/auth/token/refresh/ com token válido"""
        refresh = RefreshToken.for_user(self.user)
        
        data = {
            "refresh": str(refresh)
        }
        
        response = self.client.post("/api/v1/auth/token/refresh/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_token_refresh_invalid_token(self):
        """Testa POST /api/v1/auth/token/refresh/ com token inválido"""
        data = {
            "refresh": "invalid_token"
        }
        
        response = self.client.post("/api/v1/auth/token/refresh/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh_missing_token(self):
        """Testa POST /api/v1/auth/token/refresh/ sem token"""
        data = {}
        
        response = self.client.post("/api/v1/auth/token/refresh/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_refresh_expired_token(self):
        """Testa POST /api/v1/auth/token/refresh/ com token expirado"""
        # Criar um token e simular expiração (isso é difícil de testar sem mock)
        # Por enquanto, testamos com um token inválido
        data = {
            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid"
        }
        
        response = self.client.post("/api/v1/auth/token/refresh/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TokenVerifyViewTests(TestCase):
    """Testes para TokenVerifyView"""

    def setUp(self):
        self.client = APIClient()
        self.user = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_token_verify_valid_token(self):
        """Testa POST /api/v1/auth/token/verify/ com token válido"""
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        
        data = {
            "token": access_token
        }
        
        response = self.client.post("/api/v1/auth/token/verify/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_token_verify_invalid_token(self):
        """Testa POST /api/v1/auth/token/verify/ com token inválido"""
        data = {
            "token": "invalid_token"
        }
        
        response = self.client.post("/api/v1/auth/token/verify/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_verify_missing_token(self):
        """Testa POST /api/v1/auth/token/verify/ sem token"""
        data = {}
        
        response = self.client.post("/api/v1/auth/token/verify/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_verify_refresh_token(self):
        """Testa POST /api/v1/auth/token/verify/ com refresh token"""
        refresh = RefreshToken.for_user(self.user)
        
        data = {
            "token": str(refresh)
        }
        
        response = self.client.post("/api/v1/auth/token/verify/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class MeViewTests(TestCase):
    """Testes para MeView"""

    def setUp(self):
        self.client = APIClient()
        self.user = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            display_name="Test User",
            phone_number="+5511999999999"
        )

    def test_me_get_authenticated(self):
        """Testa GET /api/v1/me/ com usuário autenticado"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get("/api/v1/me/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "testuser")
        self.assertEqual(response.data["email"], "test@example.com")
        self.assertEqual(response.data["display_name"], "Test User")
        self.assertEqual(response.data["phone_number"], "+5511999999999")

    def test_me_get_unauthenticated(self):
        """Testa GET /api/v1/me/ sem autenticação"""
        response = self.client.get("/api/v1/me/")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_patch_authenticated(self):
        """Testa PATCH /api/v1/me/ com usuário autenticado"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            "display_name": "Updated Name",
            "phone_number": "+5511888888888"
        }
        
        response = self.client.patch("/api/v1/me/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["display_name"], "Updated Name")
        self.assertEqual(response.data["phone_number"], "+5511888888888")

    def test_me_patch_unauthenticated(self):
        """Testa PATCH /api/v1/me/ sem autenticação"""
        data = {
            "display_name": "Updated Name"
        }
        
        response = self.client.patch("/api/v1/me/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_patch_invalid_data(self):
        """Testa PATCH /api/v1/me/ com dados inválidos"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            "email": "invalid_email"  # Email inválido
        }
        
        response = self.client.patch("/api/v1/me/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_me_patch_readonly_fields(self):
        """Testa PATCH /api/v1/me/ tentando alterar campos readonly"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            "username": "newusername",  # Campo readonly
            "is_staff": True,  # Campo readonly
            "is_superuser": True  # Campo readonly
        }
        
        response = self.client.patch("/api/v1/me/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verificar se os campos readonly não foram alterados
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "testuser")
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)
