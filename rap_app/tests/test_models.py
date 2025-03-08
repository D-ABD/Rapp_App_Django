import os
import tempfile
from datetime import date, timedelta

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from ..models.base import BaseModel
from ..models.centres import Centre
from ..models.commentaires import Commentaire
from ..models.documents import Document, validate_file_extension
from ..models.entreprises import Entreprise
from ..models.evenements import Evenement
from ..models.formations import Formation
from ..models.historique_formations import HistoriqueFormation
from ..models.statut import Statut, get_default_color
from ..models.types_offre import TypeOffre

User = get_user_model()


class CentreTestCase(TestCase):
    """Tests pour le modèle Centre"""

    def setUp(self):
        self.centre = Centre.objects.create(
            nom="Centre de Formation Test",
            code_postal="75001"
        )

    def test_centre_creation(self):
        """Test de création d'un centre"""
        self.assertEqual(self.centre.nom, "Centre de Formation Test")
        self.assertEqual(self.centre.code_postal, "75001")
        self.assertIsNotNone(self.centre.created_at)
        self.assertIsNotNone(self.centre.updated_at)

    def test_centre_str(self):
        """Test de la méthode __str__"""
        self.assertEqual(str(self.centre), "Centre de Formation Test")

    def test_centre_full_address(self):
        """Test de la méthode full_address"""
        self.assertEqual(self.centre.full_address(), "Centre de Formation Test (75001)")
        
        # Test sans code postal
        centre_sans_cp = Centre.objects.create(nom="Centre Sans CP")
        self.assertEqual(centre_sans_cp.full_address(), "Centre Sans CP")

    def test_code_postal_validation(self):
        """Test de la validation du code postal"""
        # Code postal invalide (lettres)
        centre_invalide = Centre(nom="Centre Invalide", code_postal="ABCDE")
        with self.assertRaises(ValidationError):
            centre_invalide.full_clean()
            
        # Code postal invalide (longueur)
        centre_invalide2 = Centre(nom="Centre Invalide 2", code_postal="123")
        with self.assertRaises(ValidationError):
            centre_invalide2.full_clean()


class EntrepriseTestCase(TestCase):
    """Tests pour le modèle Entreprise"""

    def setUp(self):
        self.entreprise = Entreprise.objects.create(
            nom="Entreprise Test",
            secteur_activite="IT",
            contact_nom="Jean Dupont",
            contact_email="jean@example.com"
        )

    def test_entreprise_creation(self):
        """Test de création d'une entreprise"""
        self.assertEqual(self.entreprise.nom, "Entreprise Test")
        self.assertEqual(self.entreprise.secteur_activite, "IT")
        self.assertEqual(self.entreprise.contact_nom, "Jean Dupont")
        self.assertEqual(self.entreprise.contact_email, "jean@example.com")

    def test_entreprise_str(self):
        """Test de la méthode __str__"""
        self.assertEqual(str(self.entreprise), "Entreprise Test")


class StatutTestCase(TestCase):
    """Tests pour le modèle Statut"""

    def setUp(self):
        self.statut_defini = Statut.objects.create(
            nom=Statut.RECRUTEMENT_EN_COURS
        )
        self.statut_autre = Statut.objects.create(
            nom=Statut.AUTRE,
            description_autre="Statut personnalisé"
        )
        self.statut_avec_couleur = Statut.objects.create(
            nom=Statut.FORMATION_EN_COURS,
            couleur="#FF5733"
        )

    def test_statut_creation(self):
        """Test de création d'un statut"""
        self.assertEqual(self.statut_defini.nom, Statut.RECRUTEMENT_EN_COURS)
        self.assertEqual(self.statut_autre.nom, Statut.AUTRE)
        self.assertEqual(self.statut_autre.description_autre, "Statut personnalisé")

    def test_get_default_color(self):
        """Test de la fonction get_default_color"""
        self.assertEqual(get_default_color(Statut.RECRUTEMENT_EN_COURS), "#4CAF50")  # Vert
        self.assertEqual(get_default_color(Statut.FORMATION_ANNULEE), "#F44336")    # Rouge
        self.assertEqual(get_default_color("statut_inexistant"), "#607D8B")          # Couleur par défaut

    def test_couleur_par_defaut(self):
        """Test de l'attribution automatique de couleur"""
        self.assertIsNotNone(self.statut_defini.couleur)
        self.assertEqual(self.statut_defini.couleur, "#4CAF50")  # Couleur par défaut pour "recrutement_en_cours"

    def test_couleur_personnalisee(self):
        """Test de la conservation de la couleur personnalisée"""
        self.assertEqual(self.statut_avec_couleur.couleur, "#FF5733")

    def test_validation_autre(self):
        """Test de la validation pour le type 'autre'"""
        statut_invalide = Statut(nom=Statut.AUTRE)
        with self.assertRaises(ValidationError):
            statut_invalide.full_clean()

    def test_str_method(self):
        """Test de la méthode __str__"""
        self.assertEqual(str(self.statut_defini), "Recrutement en cours - #4CAF50")
        self.assertEqual(str(self.statut_autre), "Statut personnalisé - #795548")


class TypeOffreTestCase(TestCase):
    """Tests pour le modèle TypeOffre"""

    def setUp(self):
        self.type_defini = TypeOffre.objects.create(
            nom=TypeOffre.CRIF
        )
        self.type_autre = TypeOffre.objects.create(
            nom=TypeOffre.AUTRE,
            autre="Type personnalisé"
        )

    def test_type_offre_creation(self):
        """Test de création d'un type d'offre"""
        self.assertEqual(self.type_defini.nom, TypeOffre.CRIF)
        self.assertEqual(self.type_autre.nom, TypeOffre.AUTRE)
        self.assertEqual(self.type_autre.autre, "Type personnalisé")

    def test_validation_autre(self):
        """Test de la validation pour le type 'autre'"""
        type_invalide = TypeOffre(nom=TypeOffre.AUTRE)
        with self.assertRaises(ValidationError):
            type_invalide.full_clean()

    def test_str_method(self):
        """Test de la méthode __str__"""
        self.assertEqual(str(self.type_defini), "CRIF")
        self.assertEqual(str(self.type_autre), "Type personnalisé")

    def test_is_personnalise(self):
        """Test de la méthode is_personnalise"""
        self.assertFalse(self.type_defini.is_personnalise())
        self.assertTrue(self.type_autre.is_personnalise())


class FormationTestCase(TestCase):
    """Tests pour le modèle Formation"""

    def setUp(self):
        self.centre = Centre.objects.create(nom="Centre Test")
        self.statut = Statut.objects.create(nom=Statut.RECRUTEMENT_EN_COURS)
        self.type_offre = TypeOffre.objects.create(nom=TypeOffre.CRIF)
        self.user = User.objects.create_user(username="testuser", password="password")
        self.entreprise = Entreprise.objects.create(nom="Entreprise Test")
        
        # Créer une formation de base
        self.formation = Formation.objects.create(
            nom="Formation Python",
            centre=self.centre,
            statut=self.statut,
            type_offre=self.type_offre,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=90),
            prevus_crif=10,
            prevus_mp=5,
            inscrits_crif=3,
            inscrits_mp=2,
            utilisateur=self.user
        )
        
        # Ajouter une entreprise à la formation
        self.formation.entreprises.add(self.entreprise)

    def test_formation_creation(self):
        """Test de création d'une formation"""
        self.assertEqual(self.formation.nom, "Formation Python")
        self.assertEqual(self.formation.centre, self.centre)
        self.assertEqual(self.formation.statut, self.statut)
        self.assertEqual(self.formation.type_offre, self.type_offre)
        self.assertEqual(self.formation.prevus_crif, 10)
        self.assertEqual(self.formation.prevus_mp, 5)
        self.assertEqual(self.formation.inscrits_crif, 3)
        self.assertEqual(self.formation.inscrits_mp, 2)
        self.assertEqual(self.formation.utilisateur, self.user)
        self.assertEqual(self.formation.entreprises.count(), 1)

    def test_total_places(self):
        """Test de la propriété total_places"""
        self.assertEqual(self.formation.total_places, 15)  # 10 CRIF + 5 MP

    def test_total_inscrits(self):
        """Test de la propriété total_inscrits"""
        self.assertEqual(self.formation.total_inscrits, 5)  # 3 CRIF + 2 MP

    def test_a_recruter(self):
        """Test de la propriété a_recruter"""
        self.assertEqual(self.formation.a_recruter, 10)  # 15 places - 5 inscrits

    def test_saturation_calculation(self):
        """Test du calcul automatique de la saturation"""
        # Le calcul devrait être (5/15)*100 = 33.33%
        self.assertAlmostEqual(self.formation.saturation, 33.33, places=2)
        
        # Modifions les inscrits et vérifions que la saturation est recalculée
        self.formation.inscrits_crif = 8
        self.formation.save()
        self.assertAlmostEqual(self.formation.saturation, 66.67, places=2)  # (10/15)*100

    def test_is_a_recruter(self):
        """Test de la propriété is_a_recruter"""
        self.assertTrue(self.formation.is_a_recruter)  # 10 places à pourvoir
        
        # Remplir toutes les places
        self.formation.inscrits_crif = 10
        self.formation.inscrits_mp = 5
        self.formation.save()
        self.assertFalse(self.formation.is_a_recruter)  # 0 places à pourvoir

    def test_str_method(self):
        """Test de la méthode __str__"""
        self.assertEqual(str(self.formation), "Formation Python (Centre Test)")

    def test_get_evenements_par_type(self):
        """Test de la méthode get_nombre_evenements_par_type"""
        # Créer quelques événements
        Evenement.objects.create(
            formation=self.formation,
            type_evenement=Evenement.JOB_DATING,
            event_date=date.today()
        )
        Evenement.objects.create(
            formation=self.formation,
            type_evenement=Evenement.JOB_DATING,
            event_date=date.today() + timedelta(days=7)
        )
        Evenement.objects.create(
            formation=self.formation,
            type_evenement=Evenement.FORUM,
            event_date=date.today() + timedelta(days=14)
        )
        
        # Vérifier le comptage
        evenements_par_type = self.formation.get_nombre_evenements_par_type()
        self.assertEqual(len(evenements_par_type), 2)  # 2 types différents
        self.assertEqual(evenements_par_type[Evenement.JOB_DATING], 2)
        self.assertEqual(evenements_par_type[Evenement.FORUM], 1)
        
        # Vérifier que nombre_evenements est mis à jour (géré par les signaux)
        self.assertEqual(self.formation.nombre_evenements, 3)


class CommentaireTestCase(TestCase):
    """Tests pour le modèle Commentaire"""

    def setUp(self):
        # Créer les objets nécessaires
        self.centre = Centre.objects.create(nom="Centre Test")
        self.statut = Statut.objects.create(nom=Statut.RECRUTEMENT_EN_COURS)
        self.type_offre = TypeOffre.objects.create(nom=TypeOffre.CRIF)
        self.user = User.objects.create_user(username="testuser", password="password")
        
        self.formation = Formation.objects.create(
            nom="Formation Test",
            centre=self.centre,
            statut=self.statut,
            type_offre=self.type_offre,
            prevus_crif=10,
            inscrits_crif=5,
            utilisateur=self.user
        )

    def test_commentaire_creation(self):
        """Test de création d'un commentaire"""
        commentaire = Commentaire.objects.create(
            formation=self.formation,
            utilisateur=self.user,
            contenu="Ceci est un commentaire de test",
            saturation=60
        )
        
        self.assertEqual(commentaire.formation, self.formation)
        self.assertEqual(commentaire.utilisateur, self.user)
        self.assertEqual(commentaire.contenu, "Ceci est un commentaire de test")
        self.assertEqual(commentaire.saturation, 60)

    def test_str_method(self):
        """Test de la méthode __str__"""
        commentaire = Commentaire.objects.create(
            formation=self.formation,
            utilisateur=self.user,
            contenu="Test str"
        )
        expected_str = f"Commentaire de {self.user} sur {self.formation.nom} ({commentaire.created_at.strftime('%d/%m/%Y')})"
        self.assertEqual(str(commentaire), expected_str)

    def test_signal_update_formation_saturation(self):
        """Test du signal qui met à jour la saturation de la formation"""
        # Créer un commentaire avec une saturation
        commentaire = Commentaire.objects.create(
            formation=self.formation,
            utilisateur=self.user,
            contenu="Test de saturation",
            saturation=75
        )
        
        # Vérifier que la formation a été mise à jour
        self.formation.refresh_from_db()
        self.assertEqual(self.formation.saturation, 75)  # La valeur de saturation du commentaire
        self.assertEqual(self.formation.dernier_commentaire, "Test de saturation")

    def test_signal_update_dernier_commentaire(self):
        """Test du signal qui met à jour le dernier commentaire"""
        # Créer plusieurs commentaires
        commentaire1 = Commentaire.objects.create(
            formation=self.formation,
            utilisateur=self.user,
            contenu="Premier commentaire"
        )
        
        commentaire2 = Commentaire.objects.create(
            formation=self.formation,
            utilisateur=self.user,
            contenu="Deuxième commentaire"
        )
        
        # Vérifier que le dernier commentaire est bien le dernier créé
        self.formation.refresh_from_db()
        self.assertEqual(self.formation.dernier_commentaire, "Deuxième commentaire")
        
        # Supprimer le dernier commentaire et vérifier la mise à jour
        commentaire2.delete()
        self.formation.refresh_from_db()
        self.assertEqual(self.formation.dernier_commentaire, "Premier commentaire")


class EvenementTestCase(TestCase):
    """Tests pour le modèle Evenement"""

    def setUp(self):
        # Créer les objets nécessaires
        self.centre = Centre.objects.create(nom="Centre Test")
        self.statut = Statut.objects.create(nom=Statut.RECRUTEMENT_EN_COURS)
        self.type_offre = TypeOffre.objects.create(nom=TypeOffre.CRIF)
        
        self.formation = Formation.objects.create(
            nom="Formation Test",
            centre=self.centre,
            statut=self.statut,
            type_offre=self.type_offre
        )

    def test_evenement_creation(self):
        """Test de création d'un événement"""
        evenement = Evenement.objects.create(
            formation=self.formation,
            type_evenement=Evenement.JOB_DATING,
            event_date=date.today(),
            details="Détails de l'événement"
        )
        
        self.assertEqual(evenement.formation, self.formation)
        self.assertEqual(evenement.type_evenement, Evenement.JOB_DATING)
        self.assertEqual(evenement.event_date, date.today())
        self.assertEqual(evenement.details, "Détails de l'événement")

    def test_validation_autre(self):
        """Test de validation pour le type 'autre'"""
        # Sans description_autre, doit échouer
        evenement_invalide = Evenement(
            formation=self.formation,
            type_evenement=Evenement.AUTRE,
            event_date=date.today()
        )
        with self.assertRaises(ValidationError):
            evenement_invalide.full_clean()
        
        # Avec description_autre, doit réussir
        evenement_valide = Evenement(
            formation=self.formation,
            type_evenement=Evenement.AUTRE,
            description_autre="Type personnalisé",
            event_date=date.today()
        )
        evenement_valide.full_clean()  # Ne doit pas lever d'exception

    def test_str_method(self):
        """Test de la méthode __str__"""
        evenement = Evenement.objects.create(
            formation=self.formation,
            type_evenement=Evenement.JOB_DATING,
            event_date=date.today()
        )
        expected_str = f"Job dating - {date.today().strftime('%d/%m/%Y')}"
        self.assertEqual(str(evenement), expected_str)
        
        # Test sans date
        evenement_sans_date = Evenement.objects.create(
            formation=self.formation,
            type_evenement=Evenement.FORUM
        )
        self.assertEqual(str(evenement_sans_date), "Forum - Date inconnue")

    def test_signal_update_nombre_evenements(self):
        """Test des signaux qui mettent à jour nombre_evenements"""
        # Au départ, nombre_evenements doit être 0
        self.assertEqual(self.formation.nombre_evenements, 0)
        
        # Créer un événement
        evenement1 = Evenement.objects.create(
            formation=self.formation,
            type_evenement=Evenement.JOB_DATING,
            event_date=date.today()
        )
        self.formation.refresh_from_db()
        self.assertEqual(self.formation.nombre_evenements, 1)
        
        # Créer un autre événement
        evenement2 = Evenement.objects.create(
            formation=self.formation,
            type_evenement=Evenement.FORUM,
            event_date=date.today() + timedelta(days=7)
        )
        self.formation.refresh_from_db()
        self.assertEqual(self.formation.nombre_evenements, 2)
        
        # Supprimer un événement
        evenement1.delete()
        self.formation.refresh_from_db()
        self.assertEqual(self.formation.nombre_evenements, 1)


class DocumentTestCase(TestCase):
    """Tests pour le modèle Document"""

    def setUp(self):
        # Créer les objets nécessaires
        self.centre = Centre.objects.create(nom="Centre Test")
        self.statut = Statut.objects.create(nom=Statut.RECRUTEMENT_EN_COURS)
        self.type_offre = TypeOffre.objects.create(nom=TypeOffre.CRIF)
        
        self.formation = Formation.objects.create(
            nom="Formation Test",
            centre=self.centre,
            statut=self.statut,
            type_offre=self.type_offre
        )
        
        # Créer un fichier temporaire pour les tests
        self.temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        self.temp_pdf.write(b"PDF test content")
        self.temp_pdf.close()
        
        self.temp_image = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        self.temp_image.write(b"JPG test content")
        self.temp_image.close()

    def tearDown(self):
        # Supprimer les fichiers temporaires
        if os.path.exists(self.temp_pdf.name):
            os.unlink(self.temp_pdf.name)
        if os.path.exists(self.temp_image.name):
            os.unlink(self.temp_image.name)

    def test_validate_file_extension(self):
        """Test de la fonction validate_file_extension"""
        # Créer des fichiers de test
        pdf_file = SimpleUploadedFile("test.pdf", b"pdf content", content_type="application/pdf")
        jpg_file = SimpleUploadedFile("test.jpg", b"jpg content", content_type="image/jpeg")
        txt_file = SimpleUploadedFile("test.txt", b"text content", content_type="text/plain")
        
        # Tests de validation réussis
        validate_file_extension(pdf_file, Document.PDF)        # PDF pour type PDF
        validate_file_extension(jpg_file, Document.IMAGE)      # JPG pour type IMAGE
        validate_file_extension(pdf_file, Document.CONTRAT)    # PDF pour type CONTRAT
        validate_file_extension(txt_file, Document.AUTRE)      # TXT pour type AUTRE
        
        # Tests de validation échoués
        with self.assertRaises(ValidationError):
            validate_file_extension(txt_file, Document.PDF)     # TXT pour type PDF
        
        with self.assertRaises(ValidationError):
            validate_file_extension(pdf_file, Document.IMAGE)   # PDF pour type IMAGE

    def test_document_creation(self):
        """Test de création d'un document"""
        # Créer un document PDF
        with open(self.temp_pdf.name, 'rb') as f:
            document = Document.objects.create(
                formation=self.formation,
                nom_fichier="Test PDF",
                fichier=SimpleUploadedFile("test.pdf", f.read()),
                type_document=Document.PDF,
                source="Test source"
            )
        
        self.assertEqual(document.formation, self.formation)
        self.assertEqual(document.nom_fichier, "Test PDF")
        self.assertEqual(document.type_document, Document.PDF)
        self.assertEqual(document.source, "Test source")
        self.assertTrue(document.taille_fichier > 0)

    def test_str_method(self):
        """Test de la méthode __str__"""
        with open(self.temp_pdf.name, 'rb') as f:
            document = Document.objects.create(
                formation=self.formation,
                nom_fichier="Document de test",
                fichier=SimpleUploadedFile("test.pdf", f.read()),
                type_document=Document.PDF
            )
        
        self.assertEqual(str(document), "Document de test (PDF)")
        
        # Test avec un nom long
        with open(self.temp_pdf.name, 'rb') as f:
            document_long = Document.objects.create(
                formation=self.formation,
                nom_fichier="A" * 60,  # Nom > 50 caractères
                fichier=SimpleUploadedFile("test2.pdf", f.read()),
                type_document=Document.PDF
            )
        
        self.assertEqual(str(document_long), "A" * 50 + "... (PDF)")


class HistoriqueFormationTestCase(TestCase):
    """Tests pour le modèle HistoriqueFormation"""

    def setUp(self):
        # Créer les objets nécessaires
        self.centre = Centre.objects.create(nom="Centre Test")
        self.statut = Statut.objects.create(nom=Statut.RECRUTEMENT_EN_COURS)
        self.type_offre = TypeOffre.objects.create(nom=TypeOffre.CRIF)
        self.user = User.objects.create_user(username="testuser", password="password")
        
        self.formation = Formation.objects.create(
            nom="Formation Test",
            centre=self.centre,
            statut=self.statut,
            type_offre=self.type_offre,
            prevus_crif=10,
            inscrits_crif=5,
            utilisateur=self.user
        )

    def test_historique_creation(self):
        """Test de création d'un historique"""
        historique = HistoriqueFormation.objects.create(
            formation=self.formation,
            utilisateur=self.user,
            action="modification",
            ancien_statut=Statut.RECRUTEMENT_EN_COURS,
            nouveau_statut=Statut.FORMATION_EN_COURS,
            details={"prevus_crif": {"ancien": 10, "nouveau": 12}}
        )
        
        self.assertEqual(historique.formation, self.formation)
        self.assertEqual(historique.utilisateur, self.user)
        self.assertEqual(historique.action, "modification")
        self.assertEqual(historique.ancien_statut, Statut.RECRUTEMENT_EN_COURS)
        self.assertEqual(historique.nouveau_statut, Statut.FORMATION_EN_COURS)
        self.assertEqual(historique.details["prevus_crif"]["ancien"], 10)
        self.assertEqual(historique.details["prevus_crif"]["nouveau"], 12)

    def test_auto_fields_calculation(self):
        """Test du calcul automatique des champs lors de la sauvegarde"""
        historique = HistoriqueFormation.objects.create(
            formation=self.formation,
            utilisateur=self.user,
            action="modification"
        )
        
        # Vérifier que les champs liés à la formation sont bien copiés
        self.assertEqual(historique.inscrits_total, 5)
        self.assertEqual(historique.inscrits_crif, 5)
        self.assertEqual(historique.inscrits_mp, 0)
        self.assertEqual(historique.total_places, 10)
        
        # Vérifier le calcul du taux de remplissage
        self.assertEqual(historique.taux_remplissage, 50.0)  # (5/10)*100
        
        # Vérifier les champs temporels
        self.assertIsNotNone(historique.semaine)
        self.assertIsNotNone(historique.mois)
        self.assertIsNotNone(historique.annee)

    def test_str_method(self):
        """Test de la méthode __str__"""
        historique = HistoriqueFormation.objects.create(
            formation=self.formation,
            action="modification"
        )
        
        expected_str = f"Formation Test - {historique.created_at.strftime('%Y-%m-%d')}"
        self.assertEqual(str(historique), expected_str)