from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
from datetime import timedelta

from ..models import (
    Centre, TypeOffre, Statut, Formation, Evenement, 
    Commentaire, Document, Rapport, Ressource, Parametre,
    Recherche, HistoriqueFormation
)

class BaseViewTestCase(TestCase):
    """
    Classe de base pour les tests de vues avec configuration commune
    """
    def setUp(self):
        # Créer un utilisateur admin pour les tests
        User = get_user_model()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            id=uuid.uuid4()
        )
        
        # Créer un utilisateur normal
        self.user = User.objects.create_user(
            username='testuser',
            email='user@example.com',
            password='userpassword',
            id=uuid.uuid4()
        )
        
        # Client pour les requêtes
        self.client = Client()
        
        # Créer des objets de base pour les tests
        self.centre = Centre.objects.create(
            nom="Centre Test",
            code_postal="75000"
        )
        
        self.type_offre = TypeOffre.objects.create(
            nom=TypeOffre.CRIF
        )
        
        self.statut = Statut.objects.create(
            nom=Statut.RECRUTEMENT_EN_COURS,
            couleur="#FF0000"
        )
        
        # Créer une formation
        self.formation = Formation.objects.create(
            nom="Formation Test",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
            prevus_crif=20,
            prevus_mp=10,
            inscrits_crif=15,
            inscrits_mp=8
        )
        
        # Créer un événement
        self.evenement = Evenement.objects.create(
            formation=self.formation,
            type_evenement=Evenement.INFO_PRESENTIEL,
            event_date=timezone.now().date() + timedelta(days=7),
            details="Événement de test"
        )
        
        # Créer un commentaire
        self.commentaire = Commentaire.objects.create(
            formation=self.formation,
            auteur="Test Auteur",
            contenu="Commentaire de test",
            utilisateur=self.admin_user
        )
        
        # Créer un rapport
        self.rapport = Rapport.objects.create(
            formation=self.formation,
            periode=Rapport.MENSUEL,
            date_debut=timezone.now().date() - timedelta(days=30),
            date_fin=timezone.now().date(),
            total_inscrits=23,
            inscrits_crif=15,
            inscrits_mp=8,
            total_places=30
        )
        
        # Créer une ressource
        self.ressource = Ressource.objects.create(
            formation=self.formation,
            nombre_candidats=35,
            nombre_entretiens=28
        )
        
        # Créer un paramètre
        self.parametre = Parametre.objects.create(
            cle="TEST_PARAMETER",
            valeur="value_test",
            description="Paramètre de test"
        )
        
        # Créer un historique
        self.historique = HistoriqueFormation.objects.create(
            formation=self.formation,
            utilisateur=self.admin_user,
            action="Création test",
            nouveau_statut=self.statut.nom,
            inscrits_total=23,
            inscrits_crif=15,
            inscrits_mp=8,
            total_places=30
        )
        
        # Créer une recherche
        self.recherche = Recherche.objects.create(
            utilisateur=self.admin_user,
            terme_recherche="formation test",
            nombre_resultats=1
        )

class DashboardViewTestCase(BaseViewTestCase):
    """Tests pour la vue du tableau de bord"""
    
    def test_dashboard_view_not_authenticated(self):
        """Test que le tableau de bord redirige vers la page de connexion si non authentifié"""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/connexion/', response.url)
    
    def test_dashboard_view_authenticated(self):
        """Test que le tableau de bord s'affiche correctement pour un utilisateur authentifié"""
        self.client.login(username='testuser', password='userpassword')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rap_app/dashboard.html')
        
        # Vérifier que les statistiques globales sont présentes
        self.assertIn('total_formations', response.context)
        self.assertIn('formations_actives', response.context)
        self.assertIn('formations_a_venir', response.context)
        
        # Vérifier que les données récentes sont présentes
        self.assertIn('formations_recentes', response.context)
        self.assertIn('evenements_a_venir', response.context)

class FormationViewsTestCase(BaseViewTestCase):
    """Tests pour les vues liées aux formations"""
    
    def test_formation_list_view(self):
        """Test que la liste des formations s'affiche correctement"""
        self.client.login(username='testuser', password='userpassword')
        response = self.client.get(reverse('formation-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rap_app/formation_list.html')
        self.assertIn('formations', response.context)
        self.assertIn(self.formation, response.context['formations'])
    
    def test_formation_detail_view(self):
        """Test que la page de détail d'une formation s'affiche correctement"""
        self.client.login(username='testuser', password='userpassword')
        response = self.client.get(reverse('formation-detail', kwargs={'pk': self.formation.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rap_app/formation_detail.html')
        self.assertEqual(response.context['formation'], self.formation)
        
        # Vérifier que les éléments associés sont présents
        self.assertIn('evenements', response.context)
        self.assertIn('commentaires', response.context)
    
    def test_formation_create_view_as_normal_user(self):
        """Test qu'un utilisateur normal ne peut pas accéder à la création de formation"""
        self.client.login(username='testuser', password='userpassword')
        response = self.client.get(reverse('formation-create'))
        self.assertEqual(response.status_code, 403)  # Forbidden
    
    def test_formation_create_view_as_admin(self):
        """Test qu'un admin peut accéder à la création de formation"""
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('formation-create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rap_app/formation_form.html')
    
    def test_formation_update_view(self):
        """Test la mise à jour d'une formation"""
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('formation-update', kwargs={'pk': self.formation.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Test de la soumission du formulaire
        update_data = {
            'nom': 'Formation Test Modifiée',
            'centre': self.centre.pk,
            'type_offre': self.type_offre.pk,
            'statut': self.statut.pk,
            'start_date': timezone.now().date().isoformat(),
            'end_date': (timezone.now().date() + timedelta(days=60)).isoformat(),
            'prevus_crif': 25,
            'prevus_mp': 15,
            'inscrits_crif': 20,
            'inscrits_mp': 10,
            'assistante': 'Assistante Test',
            'cap': 40,
            'convocation_envoie': True,
            'entresformation': 30
        }
        
        response = self.client.post(
            reverse('formation-update', kwargs={'pk': self.formation.pk}),
            update_data,
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que la formation a été mise à jour
        self.formation.refresh_from_db()
        self.assertEqual(self.formation.nom, 'Formation Test Modifiée')
        self.assertEqual(self.formation.prevus_crif, 25)
        self.assertEqual(self.formation.inscrits_mp, 10)
    
    def test_formation_delete_view(self):
        """Test la suppression d'une formation"""
        self.client.login(username='admin', password='adminpassword')
        
        # Créer une formation spécifique pour le test de suppression
        formation_to_delete = Formation.objects.create(
            nom="Formation à supprimer",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30)
        )
        
        # Vérifier que la page de confirmation s'affiche
        response = self.client.get(reverse('formation-delete', kwargs={'pk': formation_to_delete.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rap_app/formation_confirm_delete.html')
        
        # Effectuer la suppression
        response = self.client.post(
            reverse('formation-delete', kwargs={'pk': formation_to_delete.pk}),
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que la formation a été supprimée
        with self.assertRaises(Formation.DoesNotExist):
            Formation.objects.get(pk=formation_to_delete.pk)

class CentreViewsTestCase(BaseViewTestCase):
    """Tests pour les vues liées aux centres"""
    
    def test_centre_list_view(self):
        """Test que la liste des centres s'affiche correctement"""
        self.client.login(username='testuser', password='userpassword')
        response = self.client.get(reverse('centre-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rap_app/centre_list.html')
        self.assertIn('centres', response.context)
        self.assertIn(self.centre, response.context['centres'])
    
    def test_centre_detail_view(self):
        """Test que la page de détail d'un centre s'affiche correctement"""
        self.client.login(username='testuser', password='userpassword')
        response = self.client.get(reverse('centre-detail', kwargs={'pk': self.centre.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rap_app/centre_detail.html')
        self.assertEqual(response.context['centre'], self.centre)
    
    def test_centre_create_view(self):
        """Test la création d'un centre"""
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('centre-create'))
        self.assertEqual(response.status_code, 200)
        
        # Test de la soumission du formulaire
        create_data = {
            'nom': 'Nouveau Centre',
            'code_postal': '75001',
        }
        
        response = self.client.post(
            reverse('centre-create'),
            create_data,
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que le centre a été créé
        self.assertTrue(Centre.objects.filter(nom='Nouveau Centre').exists())

class EvenementViewsTestCase(BaseViewTestCase):
    """Tests pour les vues liées aux événements"""
    
    def test_evenement_list_view(self):
        """Test que la liste des événements s'affiche correctement"""
        self.client.login(username='testuser', password='userpassword')
        response = self.client.get(reverse('evenement-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rap_app/evenement_list.html')
        self.assertIn('evenements', response.context)
        self.assertIn(self.evenement, response.context['evenements'])
    
    def test_evenement_detail_view(self):
        """Test que la page de détail d'un événement s'affiche correctement"""
        self.client.login(username='testuser', password='userpassword')
        response = self.client.get(reverse('evenement-detail', kwargs={'pk': self.evenement.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rap_app/evenement_detail.html')
        self.assertEqual(response.context['evenement'], self.evenement)
    
    def test_evenement_create_view(self):
        """Test la création d'un événement"""
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('evenement-create'))
        self.assertEqual(response.status_code, 200)
        
        # Test de la soumission du formulaire
        create_data = {
            'formation': self.formation.pk,
            'type_evenement': Evenement.JOB_DATING,
            'event_date': (timezone.now().date() + timedelta(days=14)).isoformat(),
            'details': 'Nouvel événement de test',
        }
        
        response = self.client.post(
            reverse('evenement-create'),
            create_data,
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que l'événement a été créé
        self.assertTrue(Evenement.objects.filter(details='Nouvel événement de test').exists())

class CommentaireViewsTestCase(BaseViewTestCase):
    """Tests pour les vues liées aux commentaires"""
    
    def test_commentaire_list_view(self):
        """Test que la liste des commentaires s'affiche correctement"""
        self.client.login(username='testuser', password='userpassword')
        response = self.client.get(reverse('commentaire-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rap_app/commentaire_list.html')
        self.assertIn('commentaires', response.context)
        self.assertIn(self.commentaire, response.context['commentaires'])
    
    def test_commentaire_detail_view(self):
        """Test que la page de détail d'un commentaire s'affiche correctement"""
        self.client.login(username='testuser', password='userpassword')
        response = self.client.get(reverse('commentaire-detail', kwargs={'pk': self.commentaire.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rap_app/commentaire_detail.html')
        self.assertEqual(response.context['commentaire'], self.commentaire)
    
    def test_commentaire_create_view(self):
        """Test la création d'un commentaire"""
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('commentaire-create'))
        self.assertEqual(response.status_code, 200)
        
        # Test de la soumission du formulaire
        create_data = {
            'formation': self.formation.pk,
            'auteur': 'Nouvel Auteur',
            'contenu': 'Nouveau commentaire de test',
        }
        
        response = self.client.post(
            reverse('commentaire-create'),
            create_data,
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que le commentaire a été créé
        self.assertTrue(Commentaire.objects.filter(contenu='Nouveau commentaire de test').exists())

class RapportViewsTestCase(BaseViewTestCase):
    """Tests pour les vues liées aux rapports"""
    
    def test_rapport_list_view(self):
        """Test que la liste des rapports s'affiche correctement"""
        self.client.login(username='testuser', password='userpassword')
        response = self.client.get(reverse('rapport-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rap_app/rapport_list.html')
        self.assertIn('rapports', response.context)
        self.assertIn(self.rapport, response.context['rapports'])
    
    def test_rapport_detail_view(self):
        """Test que la page de détail d'un rapport s'affiche correctement"""
        self.client.login(username='testuser', password='userpassword')
        response = self.client.get(reverse('rapport-detail', kwargs={'pk': self.rapport.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rap_app/rapport_detail.html')
        self.assertEqual(response.context['rapport'], self.rapport)
    
    def test_rapport_create_view(self):
        """Test la création d'un rapport"""
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('rapport-create'))
        self.assertEqual(response.status_code, 200)
        
        # Test de la soumission du formulaire
        create_data = {
            'formation': self.formation.pk,
            'periode': Rapport.HEBDOMADAIRE,
            'date_debut': (timezone.now().date() - timedelta(days=7)).isoformat(),
            'date_fin': timezone.now().date().isoformat(),
            'total_inscrits': 20,
            'inscrits_crif': 12,
            'inscrits_mp': 8,
            'total_places': 30,
            'nombre_evenements': 2,
            'nombre_candidats': 25,
            'nombre_entretiens': 18,
        }
        
        response = self.client.post(
            reverse('rapport-create'),
            create_data,
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que le rapport a été créé
        self.assertTrue(Rapport.objects.filter(periode=Rapport.HEBDOMADAIRE, total_inscrits=20).exists())

class HistoriqueFormationViewsTestCase(BaseViewTestCase):
    """Tests pour les vues liées aux historiques de formation"""
    
    def test_historique_list_view(self):
        """Test que la liste des historiques s'affiche correctement"""
        self.client.login(username='testuser', password='userpassword')
        response = self.client.get(reverse('historique-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rap_app/historiqueformation_list.html')
        self.assertIn('historiques', response.context)
        self.assertIn(self.historique, response.context['historiques'])
    
    def test_historique_detail_view(self):
        """Test que la page de détail d'un historique s'affiche correctement"""
        self.client.login(username='testuser', password='userpassword')
        response = self.client.get(reverse('historique-detail', kwargs={'pk': self.historique.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rap_app/historiqueformation_detail.html')
        self.assertEqual(response.context['historique'], self.historique)

class ParametreViewsTestCase(BaseViewTestCase):
    """Tests pour les vues liées aux paramètres"""
    
    def test_parametre_list_view(self):
        """Test que la liste des paramètres s'affiche correctement"""
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('parametre-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rap_app/parametre_list.html')
        self.assertIn('parametres', response.context)
        self.assertIn(self.parametre, response.context['parametres'])
    
    def test_parametre_update_view(self):
        """Test la mise à jour d'un paramètre"""
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('parametre-update', kwargs={'pk': self.parametre.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Test de la soumission du formulaire
        update_data = {
            'valeur': 'nouvelle_valeur_test',
            'description': 'Description mise à jour'
        }
        
        response = self.client.post(
            reverse('parametre-update', kwargs={'pk': self.parametre.pk}),
            update_data,
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que le paramètre a été mis à jour
        self.parametre.refresh_from_db()
        self.assertEqual(self.parametre.valeur, 'nouvelle_valeur_test')
        self.assertEqual(self.parametre.description, 'Description mise à jour')

class RessourceViewsTestCase(BaseViewTestCase):
    """Tests pour les vues liées aux ressources"""
    
    def test_ressource_list_view(self):
        """Test que la liste des ressources s'affiche correctement"""
        self.client.login(username='testuser', password='userpassword')
        response = self.client.get(reverse('ressource-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rap_app/ressource_list.html')
        self.assertIn('ressources', response.context)
        self.assertIn(self.ressource, response.context['ressources'])
    
    def test_ressource_detail_view(self):
        """Test que la page de détail d'une ressource s'affiche correctement"""
        self.client.login(username='testuser', password='userpassword')
        response = self.client.get(reverse('ressource-detail', kwargs={'pk': self.ressource.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rap_app/ressource_detail.html')
        self.assertEqual(response.context['ressource'], self.ressource)
    
    def test_ressource_update_view(self):
        """Test la mise à jour d'une ressource"""
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('ressource-update', kwargs={'pk': self.ressource.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Test de la soumission du formulaire
        update_data = {
            'formation': self.formation.pk,
            'nombre_candidats': 40,
            'nombre_entretiens': 32
        }
        
        response = self.client.post(
            reverse('ressource-update', kwargs={'pk': self.ressource.pk}),
            update_data,
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que la ressource a été mise à jour
        self.ressource.refresh_from_db()
        self.assertEqual(self.ressource.nombre_candidats, 40)
        self.assertEqual(self.ressource.nombre_entretiens, 32)

class AuthenticationViewsTestCase(BaseViewTestCase):
    """Tests pour les vues liées à l'authentification"""
    
    def test_login_view(self):
        """Test que la page de connexion s'affiche correctement"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        
        # Test de la connexion
        login_data = {
            'username': 'testuser',
            'password': 'userpassword'
        }
        
        response = self.client.post(
            reverse('login'),
            login_data,
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)
    
    def test_logout_view(self):
        """Test que la déconnexion fonctionne correctement"""
        self.client.login(username='testuser', password='userpassword')
        
        # Vérifier que l'utilisateur est connecté
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Déconnexion
        response = self.client.get(reverse('logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que l'utilisateur est déconnecté
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirection vers la page de connexion