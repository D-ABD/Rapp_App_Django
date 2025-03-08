from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
import uuid

from ..models import (
    BaseModel, Centre, Statut, TypeOffre, Utilisateur,
    Formation, Commentaire, Ressource, Evenement, 
    Document, HistoriqueFormation, Rapport, Parametre, Recherche
)


class CentreTestCase(TestCase):
    def setUp(self):
        self.centre = Centre.objects.create(
            nom="Centre de Test",
            code_postal="75001"
        )

    def test_str_representation(self):
        self.assertEqual(str(self.centre), "Centre de Test")
    
    def test_code_postal_validation(self):
        # Code postal valide
        self.centre.code_postal = "75001"
        self.centre.full_clean()  # Ne devrait pas lever d'exception
        
        # Code postal invalide
        self.centre.code_postal = "7500A"
        with self.assertRaises(ValidationError):
            self.centre.full_clean()


class StatutTestCase(TestCase):
    def setUp(self):
        self.statut = Statut.objects.create(
            nom=Statut.FORMATION_EN_COURS,
            couleur="#FF0000"
        )
        self.statut_autre = Statut.objects.create(
            nom=Statut.AUTRE,
            couleur="#00FF00",
            description_autre="Statut personnalisé"
        )

    def test_str_representation(self):
        self.assertEqual(str(self.statut), "Formation en cours - #FF0000")
        self.assertEqual(str(self.statut_autre), "Statut personnalisé - #00FF00")
    
    def test_autre_validation(self):
        # Création d'un statut 'autre' sans description devrait échouer
        with self.assertRaises(ValidationError):
            Statut.objects.create(
                nom=Statut.AUTRE,
                couleur="#0000FF"
            )


class TypeOffreTestCase(TestCase):
    def setUp(self):
        self.type_offre = TypeOffre.objects.create(
            nom=TypeOffre.CRIF
        )
        self.type_offre_autre = TypeOffre.objects.create(
            nom=TypeOffre.AUTRE,
            autre="Type d'offre personnalisé"
        )

    def test_str_representation(self):
        self.assertEqual(str(self.type_offre), "CRIF")
        self.assertEqual(str(self.type_offre_autre), "Type d'offre personnalisé")
    
    def test_autre_validation(self):
        # Création d'un type d'offre 'autre' sans description devrait échouer
        with self.assertRaises(ValidationError):
            TypeOffre.objects.create(
                nom=TypeOffre.AUTRE
            )


class UtilisateurTestCase(TestCase):
    def setUp(self):
        self.utilisateur = Utilisateur.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
            first_name="Test",
            last_name="User",
            role="Testeur"
        )

    def test_str_representation(self):
        self.assertEqual(str(self.utilisateur), "Test User")
        
        # Utilisateur sans nom
        user_sans_nom = Utilisateur.objects.create_user(
            username="useronly",
            password="password123"
        )
        self.assertEqual(str(user_sans_nom), "useronly")


class FormationTestCase(TestCase):
    def setUp(self):
        self.centre = Centre.objects.create(nom="Centre de Test")
        self.type_offre = TypeOffre.objects.create(nom=TypeOffre.CRIF)
        self.statut = Statut.objects.create(nom=Statut.RECRUTEMENT_EN_COURS, couleur="#FF0000")
        
        self.formation = Formation.objects.create(
            nom="Formation Test",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=90),
            prevus_crif=15,
            prevus_mp=5,
            inscrits_crif=10,
            inscrits_mp=3
        )

    def test_str_representation(self):
        self.assertEqual(str(self.formation), "Formation Test")
    
    def test_total_places(self):
        self.assertEqual(self.formation.total_places, 20)
    
    def test_inscrits_total(self):
        self.assertEqual(self.formation.inscrits_total, 13)
    
    def test_a_recruter(self):
        self.assertEqual(self.formation.a_recruter, 7)
    
    def test_taux_remplissage(self):
        self.assertEqual(self.formation.taux_remplissage, 65.0)
    
    def test_est_active(self):
        self.assertTrue(self.formation.est_active)
        
        # Formation passée
        formation_passee = Formation.objects.create(
            nom="Formation Passée",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut,
            start_date=timezone.now().date() - timedelta(days=180),
            end_date=timezone.now().date() - timedelta(days=90)
        )
        self.assertFalse(formation_passee.est_active)
    
    def test_validation_dates(self):
        # Date de fin antérieure à la date de début
        formation_invalide = Formation(
            nom="Formation Invalide",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() - timedelta(days=1)
        )
        with self.assertRaises(ValidationError):
            formation_invalide.full_clean()
    
    def test_formations_actives(self):
        # Ajouter une formation passée
        Formation.objects.create(
            nom="Formation Passée",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut,
            start_date=timezone.now().date() - timedelta(days=180),
            end_date=timezone.now().date() - timedelta(days=90)
        )
        
        # Vérifier que le manager personnalisé fonctionne
        actives = Formation.objects.formations_actives()
        self.assertEqual(actives.count(), 1)
        self.assertEqual(actives[0].nom, "Formation Test")


class CommentaireTestCase(TestCase):
    def setUp(self):
        self.centre = Centre.objects.create(nom="Centre de Test")
        self.type_offre = TypeOffre.objects.create(nom=TypeOffre.CRIF)
        self.statut = Statut.objects.create(nom=Statut.RECRUTEMENT_EN_COURS, couleur="#FF0000")
        self.utilisateur = Utilisateur.objects.create_user(username="testuser")
        
        self.formation = Formation.objects.create(
            nom="Formation Test",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut
        )
        
        self.commentaire = Commentaire.objects.create(
            formation=self.formation,
            auteur="Jean Dupont",
            contenu="Ceci est un commentaire de test",
            utilisateur=self.utilisateur
        )

    def test_str_representation(self):
        self.assertEqual(str(self.commentaire), f"Commentaire de {self.utilisateur} pour la formation Formation Test")


class RessourceTestCase(TestCase):
    def setUp(self):
        self.centre = Centre.objects.create(nom="Centre de Test")
        self.type_offre = TypeOffre.objects.create(nom=TypeOffre.CRIF)
        self.statut = Statut.objects.create(nom=Statut.RECRUTEMENT_EN_COURS, couleur="#FF0000")
        
        self.formation = Formation.objects.create(
            nom="Formation Test",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut,
            inscrits_crif=8,
            inscrits_mp=4
        )
        
        self.ressource = Ressource.objects.create(
            formation=self.formation,
            nombre_candidats=20,
            nombre_entretiens=15
        )

    def test_nombre_inscrits(self):
        self.assertEqual(self.ressource.nombre_inscrits, 12)
    
    def test_taux_transformation(self):
        self.assertEqual(self.ressource.taux_transformation, 60.0)  # 12/20 * 100
        
        # Test avec nombre_candidats à 0
        self.ressource.nombre_candidats = 0
        self.ressource.save()
        self.assertEqual(self.ressource.taux_transformation, 0)
    
    def test_str_representation(self):
        self.assertEqual(str(self.ressource), "Ressource pour Formation Test")
        
        # Test sans formation associée
        ressource_sans_formation = Ressource.objects.create(
            nombre_candidats=10
        )
        self.assertEqual(str(ressource_sans_formation), "Ressource pour Formation inconnue")


class EvenementTestCase(TestCase):
    def setUp(self):
        self.centre = Centre.objects.create(nom="Centre de Test")
        self.type_offre = TypeOffre.objects.create(nom=TypeOffre.CRIF)
        self.statut = Statut.objects.create(nom=Statut.RECRUTEMENT_EN_COURS, couleur="#FF0000")
        
        self.formation = Formation.objects.create(
            nom="Formation Test",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut
        )
        
        self.evenement = Evenement.objects.create(
            formation=self.formation,
            type_evenement=Evenement.INFO_PRESENTIEL,
            event_date=timezone.now().date(),
            details="Détails de l'événement"
        )
        
        self.evenement_autre = Evenement.objects.create(
            formation=self.formation,
            type_evenement=Evenement.AUTRE,
            event_date=timezone.now().date(),
            description_autre="Type d'événement personnalisé"
        )

    def test_str_representation(self):
        self.assertEqual(
            str(self.evenement), 
            f"Information collective présentiel - {timezone.now().date()}"
        )
    
    def test_autre_validation(self):
        # Création d'un événement 'autre' sans description devrait échouer
        with self.assertRaises(ValidationError):
            Evenement.objects.create(
                formation=self.formation,
                type_evenement=Evenement.AUTRE,
                event_date=timezone.now().date()
            )
    
    def test_update_ressource_count(self):
        # Vérifier si le nombre d'événements est mis à jour
        ressource, created = Ressource.objects.get_or_create(formation=self.formation)
        self.assertEqual(ressource.nombre_evenements, 2)  # 2 événements ont été créés
        
        # Créer un nouvel événement
        Evenement.objects.create(
            formation=self.formation,
            type_evenement=Evenement.JOB_DATING,
            event_date=timezone.now().date()
        )
        
        # Vérifier que le compteur est mis à jour
        ressource.refresh_from_db()
        self.assertEqual(ressource.nombre_evenements, 3)


class DocumentTestCase(TestCase):
    def setUp(self):
        self.centre = Centre.objects.create(nom="Centre de Test")
        self.type_offre = TypeOffre.objects.create(nom=TypeOffre.CRIF)
        self.statut = Statut.objects.create(nom=Statut.RECRUTEMENT_EN_COURS, couleur="#FF0000")
        
        self.formation = Formation.objects.create(
            nom="Formation Test",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut
        )
        
        self.document = Document.objects.create(
            formation=self.formation,
            nom_fichier="document_test.pdf",
            fichier="formations/documents/test.pdf",
            source="Source externe"
        )

    def test_str_representation(self):
        self.assertEqual(str(self.document), "document_test.pdf")


class HistoriqueFormationTestCase(TestCase):
    def setUp(self):
        self.centre = Centre.objects.create(nom="Centre de Test")
        self.type_offre = TypeOffre.objects.create(nom=TypeOffre.CRIF)
        self.statut_initial = Statut.objects.create(nom=Statut.RECRUTEMENT_EN_COURS, couleur="#FF0000")
        self.statut_final = Statut.objects.create(nom=Statut.FORMATION_EN_COURS, couleur="#00FF00")
        self.utilisateur = Utilisateur.objects.create_user(username="testuser")
        
        self.formation = Formation.objects.create(
            nom="Formation Test",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut_final
        )
        
        self.historique = HistoriqueFormation.objects.create(
            formation=self.formation,
            utilisateur=self.utilisateur,
            action="Modification du statut",
            ancien_statut=self.statut_initial.nom,
            nouveau_statut=self.statut_final.nom,
            inscrits_total=12,
            inscrits_crif=8,
            inscrits_mp=4,
            total_places=20,
            semaine=timezone.now().isocalendar()[1],
            mois=timezone.now().month,
            annee=timezone.now().year
        )

    def test_str_representation(self):
        self.assertEqual(
            str(self.historique), 
            f"Formation Test - {self.historique.created_at.strftime('%Y-%m-%d')}"
        )
    
    def test_taux_remplissage(self):
        self.assertEqual(self.historique.taux_remplissage, 60.0)  # 12/20 * 100
        
        # Test avec total_places à 0
        self.historique.total_places = 0
        self.assertEqual(self.historique.taux_remplissage, 0)


class RapportTestCase(TestCase):
    def setUp(self):
        self.centre = Centre.objects.create(nom="Centre de Test")
        self.type_offre = TypeOffre.objects.create(nom=TypeOffre.CRIF)
        self.statut = Statut.objects.create(nom=Statut.RECRUTEMENT_EN_COURS, couleur="#FF0000")
        
        self.formation = Formation.objects.create(
            nom="Formation Test",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut
        )
        
        self.rapport = Rapport.objects.create(
            formation=self.formation,
            periode=Rapport.MENSUEL,
            date_debut=timezone.now().date() - timedelta(days=30),
            date_fin=timezone.now().date(),
            total_inscrits=15,
            inscrits_crif=10,
            inscrits_mp=5,
            total_places=20,
            nombre_evenements=3,
            nombre_candidats=25,
            nombre_entretiens=18
        )

    def test_str_representation(self):
        self.assertEqual(
            str(self.rapport), 
            f"Rapport Formation Test - Mensuel ({self.rapport.date_debut} à {self.rapport.date_fin})"
        )
    
    def test_taux_remplissage(self):
        self.assertEqual(self.rapport.taux_remplissage, 75.0)  # 15/20 * 100
    
    def test_taux_transformation(self):
        self.assertEqual(self.rapport.taux_transformation, 60.0)  # 15/25 * 100
    
    def test_validation_dates(self):
        # Date de fin antérieure à la date de début
        rapport_invalide = Rapport(
            formation=self.formation,
            periode=Rapport.MENSUEL,
            date_debut=timezone.now().date(),
            date_fin=timezone.now().date() - timedelta(days=1),
            total_inscrits=15,
            total_places=20
        )
        with self.assertRaises(ValidationError):
            rapport_invalide.full_clean()


class ParametreTestCase(TestCase):
    def setUp(self):
        self.parametre = Parametre.objects.create(
            cle="email_notification",
            valeur="admin@example.com",
            description="Email pour les notifications système"
        )

    def test_str_representation(self):
        self.assertEqual(str(self.parametre), "email_notification")


class RechercheTestCase(TestCase):
    def setUp(self):
        self.centre = Centre.objects.create(nom="Centre de Test")
        self.type_offre = TypeOffre.objects.create(nom=TypeOffre.CRIF)
        self.statut = Statut.objects.create(nom=Statut.RECRUTEMENT_EN_COURS, couleur="#FF0000")
        self.utilisateur = Utilisateur.objects.create_user(username="testuser")
        
        self.recherche = Recherche.objects.create(
            utilisateur=self.utilisateur,
            terme_recherche="formation python",
            filtre_centre=self.centre,
            filtre_type_offre=self.type_offre,
            filtre_statut=self.statut,
            date_debut=timezone.now().date() - timedelta(days=30),
            date_fin=timezone.now().date() + timedelta(days=30),
            nombre_resultats=5,
            temps_execution=0.324,
            adresse_ip="127.0.0.1",
            user_agent="Mozilla/5.0"
        )
        
        self.recherche_sans_resultats = Recherche.objects.create(
            terme_recherche="formation inexistante",
            nombre_resultats=0
        )

    def test_str_representation(self):
        terme = self.recherche.terme_recherche or "Sans terme"
        utilisateur = self.recherche.utilisateur or "Anonyme"
        self.assertEqual(
            str(self.recherche), 
            f"Recherche '{terme}' par {utilisateur} ({self.recherche.nombre_resultats} résultats)"
        )
        
        terme = self.recherche_sans_resultats.terme_recherche or "Sans terme"
        utilisateur = self.recherche_sans_resultats.utilisateur or "Anonyme"
        self.assertEqual(
            str(self.recherche_sans_resultats), 
            f"Recherche '{terme}' par {utilisateur} ({self.recherche_sans_resultats.nombre_resultats} résultats)"
        )
    
    def test_a_trouve_resultats(self):
        self.assertTrue(self.recherche.a_trouve_resultats)
        self.assertFalse(self.recherche_sans_resultats.a_trouve_resultats)