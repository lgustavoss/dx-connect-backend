from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.exceptions import ValidationError

Agent = get_user_model()


class AgentModelTests(TestCase):
    """Testes para o modelo Agent"""

    def test_agent_creation_with_required_fields(self):
        """Testa criação de agente com campos obrigatórios"""
        agent = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.assertEqual(agent.username, "testuser")
        self.assertEqual(agent.email, "test@example.com")
        self.assertTrue(agent.check_password("testpass123"))
        self.assertTrue(agent.is_active)
        self.assertFalse(agent.is_staff)
        self.assertFalse(agent.is_superuser)

    def test_agent_creation_with_optional_fields(self):
        """Testa criação de agente com campos opcionais"""
        agent = Agent.objects.create_user(
            username="testuser2",
            email="test2@example.com",
            password="testpass123",
            display_name="Test User",
            phone_number="+5511999999999",
            first_name="Test",
            last_name="User"
        )
        
        self.assertEqual(agent.display_name, "Test User")
        self.assertEqual(agent.phone_number, "+5511999999999")
        self.assertEqual(agent.first_name, "Test")
        self.assertEqual(agent.last_name, "User")

    def test_agent_str_method_with_display_name(self):
        """Testa método __str__ quando display_name está definido"""
        agent = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            display_name="Test Display Name"
        )
        
        self.assertEqual(str(agent), "Test Display Name")

    def test_agent_str_method_without_display_name(self):
        """Testa método __str__ quando display_name não está definido"""
        agent = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.assertEqual(str(agent), "testuser")

    def test_agent_str_method_with_empty_display_name(self):
        """Testa método __str__ quando display_name está vazio"""
        agent = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            display_name=""
        )
        
        self.assertEqual(str(agent), "testuser")

    def test_agent_is_active_default(self):
        """Testa se is_active é True por padrão"""
        agent = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.assertTrue(agent.is_active)

    def test_agent_is_active_can_be_false(self):
        """Testa se is_active pode ser definido como False"""
        agent = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            is_active=False
        )
        
        self.assertFalse(agent.is_active)

    def test_agent_phone_number_optional(self):
        """Testa se phone_number é opcional"""
        agent = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.assertEqual(agent.phone_number, "")

    def test_agent_display_name_optional(self):
        """Testa se display_name é opcional"""
        agent = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.assertEqual(agent.display_name, "")

    def test_agent_username_required(self):
        """Testa se username é obrigatório"""
        with self.assertRaises(TypeError):
            Agent.objects.create_user(
                email="test@example.com",
                password="testpass123"
            )

    def test_agent_email_optional(self):
        """Testa se email é opcional"""
        agent = Agent.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        
        self.assertEqual(agent.username, "testuser")
        self.assertEqual(agent.email, "")

    def test_agent_password_optional(self):
        """Testa se password é opcional"""
        agent = Agent.objects.create_user(
            username="testuser",
            email="test@example.com"
        )
        
        self.assertEqual(agent.username, "testuser")
        self.assertEqual(agent.email, "test@example.com")
        self.assertFalse(agent.has_usable_password())

    def test_agent_superuser_creation(self):
        """Testa criação de superusuário"""
        agent = Agent.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123"
        )
        
        self.assertTrue(agent.is_staff)
        self.assertTrue(agent.is_superuser)
        self.assertTrue(agent.is_active)

    def test_agent_permissions_meta(self):
        """Testa se as permissões customizadas estão definidas"""
        permissions = Agent._meta.permissions
        permission_names = [perm[0] for perm in permissions]
        
        self.assertIn("manage_auth", permission_names)

    def test_agent_unique_username(self):
        """Testa se username deve ser único"""
        Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        with self.assertRaises(Exception):  # IntegrityError ou ValidationError
            Agent.objects.create_user(
                username="testuser",
                email="test2@example.com",
                password="testpass123"
            )

    def test_agent_email_not_unique(self):
        """Testa se email não precisa ser único"""
        Agent.objects.create_user(
            username="testuser1",
            email="test@example.com",
            password="testpass123"
        )
        
        # Deve funcionar sem erro
        agent2 = Agent.objects.create_user(
            username="testuser2",
            email="test@example.com",
            password="testpass123"
        )
        
        self.assertEqual(agent2.email, "test@example.com")
