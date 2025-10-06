from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

Agent = get_user_model()


class PermissionListViewTests(TestCase):
    """Testes para PermissionListView"""

    def setUp(self):
        self.client = APIClient()
        self.user = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_permission_list_get_authenticated(self):
        """Testa GET /api/v1/authz/permissions/ com usuário autenticado"""
        response = self.client.get("/api/v1/authz/permissions/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)

    def test_permission_list_get_unauthenticated(self):
        """Testa GET /api/v1/authz/permissions/ sem autenticação"""
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/v1/authz/permissions/")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permission_list_data_structure(self):
        """Testa estrutura dos dados retornados"""
        response = self.client.get("/api/v1/authz/permissions/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if response.data:
            permission = response.data[0]
            self.assertIn("id", permission)
            self.assertIn("name", permission)
            self.assertIn("codename", permission)
            self.assertIn("app_label", permission)
            self.assertIn("model", permission)


class GroupListCreateViewTests(TestCase):
    """Testes para GroupListCreateView"""

    def setUp(self):
        self.client = APIClient()
        self.user = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        # Adicionar permissão para gerenciar auth
        permission = Permission.objects.get(codename="manage_auth")
        self.user.user_permissions.add(permission)
        self.client.force_authenticate(user=self.user)

    def test_group_list_get_authenticated_with_permission(self):
        """Testa GET /api/v1/authz/groups/ com usuário autenticado e permissão"""
        response = self.client.get("/api/v1/authz/groups/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_group_list_get_without_permission(self):
        """Testa GET /api/v1/authz/groups/ sem permissão"""
        # Remover permissão
        permission = Permission.objects.get(codename="manage_auth")
        self.user.user_permissions.remove(permission)
        
        response = self.client.get("/api/v1/authz/groups/")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_group_create_post_authenticated_with_permission(self):
        """Testa POST /api/v1/authz/groups/ com usuário autenticado e permissão"""
        data = {
            "name": "Novo Grupo",
            "permissions": []
        }
        
        response = self.client.post("/api/v1/authz/groups/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Novo Grupo")

    def test_group_create_post_with_permissions(self):
        """Testa POST /api/v1/authz/groups/ com permissões"""
        permission = Permission.objects.first()
        data = {
            "name": "Grupo com Permissões",
            "permissions": [permission.id]
        }
        
        response = self.client.post("/api/v1/authz/groups/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Grupo com Permissões")

    def test_group_create_post_invalid_data(self):
        """Testa POST /api/v1/authz/groups/ com dados inválidos"""
        data = {"invalid": "data"}
        
        response = self.client.post("/api/v1/authz/groups/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_group_create_post_without_permission(self):
        """Testa POST /api/v1/authz/groups/ sem permissão"""
        # Remover permissão
        permission = Permission.objects.get(codename="manage_auth")
        self.user.user_permissions.remove(permission)
        
        data = {"name": "Novo Grupo"}
        
        response = self.client.post("/api/v1/authz/groups/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class GroupDetailViewTests(TestCase):
    """Testes para GroupDetailView"""

    def setUp(self):
        self.client = APIClient()
        self.user = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        # Adicionar permissão para gerenciar auth
        permission = Permission.objects.get(codename="manage_auth")
        self.user.user_permissions.add(permission)
        self.client.force_authenticate(user=self.user)
        
        # Criar grupo para testes
        self.group = Group.objects.create(name="Grupo Teste")

    def test_group_detail_get_authenticated_with_permission(self):
        """Testa GET /api/v1/authz/groups/{id}/ com usuário autenticado e permissão"""
        response = self.client.get(f"/api/v1/authz/groups/{self.group.id}/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Grupo Teste")

    def test_group_detail_get_nonexistent(self):
        """Testa GET /api/v1/authz/groups/{id}/ com grupo inexistente"""
        response = self.client.get("/api/v1/authz/groups/99999/")
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_group_detail_patch_authenticated_with_permission(self):
        """Testa PATCH /api/v1/authz/groups/{id}/ com usuário autenticado e permissão"""
        data = {"name": "Grupo Atualizado"}
        
        response = self.client.patch(f"/api/v1/authz/groups/{self.group.id}/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Grupo Atualizado")

    def test_group_detail_patch_with_permissions(self):
        """Testa PATCH /api/v1/authz/groups/{id}/ atualizando permissões"""
        permission = Permission.objects.first()
        data = {
            "name": "Grupo Atualizado",
            "permissions": [permission.id]
        }
        
        response = self.client.patch(f"/api/v1/authz/groups/{self.group.id}/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Grupo Atualizado")

    def test_group_detail_patch_invalid_data(self):
        """Testa PATCH /api/v1/authz/groups/{id}/ com dados inválidos"""
        data = {"permissions": ["invalid"]}  # ID de permissão inválido
        
        response = self.client.patch(f"/api/v1/authz/groups/{self.group.id}/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_group_detail_delete_authenticated_with_permission(self):
        """Testa DELETE /api/v1/authz/groups/{id}/ com usuário autenticado e permissão"""
        response = self.client.delete(f"/api/v1/authz/groups/{self.group.id}/")
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Group.objects.filter(id=self.group.id).exists())

    def test_group_detail_delete_without_permission(self):
        """Testa DELETE /api/v1/authz/groups/{id}/ sem permissão"""
        # Remover permissão
        permission = Permission.objects.get(codename="manage_auth")
        self.user.user_permissions.remove(permission)
        
        response = self.client.delete(f"/api/v1/authz/groups/{self.group.id}/")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AgentGroupsViewTests(TestCase):
    """Testes para AgentGroupsView"""

    def setUp(self):
        self.client = APIClient()
        self.user = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        # Adicionar permissão para gerenciar auth
        permission = Permission.objects.get(codename="manage_auth")
        self.user.user_permissions.add(permission)
        self.client.force_authenticate(user=self.user)
        
        # Criar outro usuário para testes
        self.other_user = Agent.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="testpass123"
        )
        
        # Criar grupos para testes
        self.group1 = Group.objects.create(name="Grupo 1")
        self.group2 = Group.objects.create(name="Grupo 2")

    def test_agent_groups_get_authenticated_with_permission(self):
        """Testa GET /api/v1/authz/agents/{id}/groups/ com usuário autenticado e permissão"""
        # Adicionar grupos ao usuário
        self.other_user.groups.add(self.group1, self.group2)
        
        response = self.client.get(f"/api/v1/authz/agents/{self.other_user.id}/groups/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 2)

    def test_agent_groups_get_nonexistent_agent(self):
        """Testa GET /api/v1/authz/agents/{id}/groups/ com agente inexistente"""
        response = self.client.get("/api/v1/authz/agents/99999/groups/")
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_agent_groups_patch_authenticated_with_permission(self):
        """Testa PATCH /api/v1/authz/agents/{id}/groups/ com usuário autenticado e permissão"""
        data = {"group_ids": [self.group1.id, self.group2.id]}
        
        response = self.client.patch(f"/api/v1/authz/agents/{self.other_user.id}/groups/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 2)

    def test_agent_groups_patch_empty_groups(self):
        """Testa PATCH /api/v1/authz/agents/{id}/groups/ removendo todos os grupos"""
        # Adicionar grupos primeiro
        self.other_user.groups.add(self.group1, self.group2)
        
        data = {"group_ids": []}
        
        response = self.client.patch(f"/api/v1/authz/agents/{self.other_user.id}/groups/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_agent_groups_patch_invalid_data(self):
        """Testa PATCH /api/v1/authz/agents/{id}/groups/ com dados inválidos"""
        data = {"invalid": "data"}
        
        response = self.client.patch(f"/api/v1/authz/agents/{self.other_user.id}/groups/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_agent_groups_patch_without_permission(self):
        """Testa PATCH /api/v1/authz/agents/{id}/groups/ sem permissão"""
        # Remover permissão
        permission = Permission.objects.get(codename="manage_auth")
        self.user.user_permissions.remove(permission)
        
        data = {"group_ids": [self.group1.id]}
        
        response = self.client.patch(f"/api/v1/authz/agents/{self.other_user.id}/groups/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_agent_groups_patch_nonexistent_agent(self):
        """Testa PATCH /api/v1/authz/agents/{id}/groups/ com agente inexistente"""
        data = {"group_ids": [self.group1.id]}
        
        response = self.client.patch("/api/v1/authz/agents/99999/groups/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
