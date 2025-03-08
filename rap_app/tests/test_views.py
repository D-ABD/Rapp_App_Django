from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from ..models import Centre
from ..views.centres_views import CentreListView


class CentreListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Créer des données de test
        cls.centre1 = Centre.objects.create(nom="Centre 1", code_postal="75001")
        cls.centre2 = Centre.objects.create(nom="Centre 2", code_postal="75002")
        
        # Créer un utilisateur avec les permissions nécessaires
        cls.user = User.objects.create_user(username="testuser", password="testpass")
        permission = Permission.objects.get(codename="view_centre")
        cls.user.user_permissions.add(permission)

    def setUp(self):
        # Simuler une requête HTTP
        self.factory = RequestFactory()



    def test_view_uses_correct_template(self):
        # Tester que le bon template est utilisé
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("centre-list"))
        self.assertTemplateUsed(response, "templates/centres/centre_list.html")

    def test_view_context_data(self):
        # Tester que les données de contexte sont correctes
        request = self.factory.get(reverse("centre-list"))
        request.user = self.user
        response = CentreListView.as_view()(request)
        
        self.assertIn("centres", response.context_data)
        self.assertEqual(len(response.context_data["centres"]), 2)

    def test_view_filters_by_code_postal(self):
        # Tester le filtre par code postal
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("centre-list") + "?code_postal=75001")
        self.assertEqual(len(response.context_data["centres"]), 1)
        self.assertEqual(response.context_data["centres"][0].code_postal, "75001")   