from django.db import models


class BaseModel(models.Model):
    """Modèle de base avec champs communs"""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    class Meta:
        abstract = True

----------------------------------------------------------------------
----------------------------------------------------------------------
from django.db import models
from django.core.validators import RegexValidator
from django.urls import reverse
from .base import BaseModel


class Centre(BaseModel):
    """Centre de formation"""
    nom = models.CharField(max_length=255, verbose_name="Nom du centre")
    code_postal = models.CharField(
        max_length=10, 
        null=True, 
        blank=True, 
        verbose_name="Code postal",
        validators=[RegexValidator(regex=r'^\d{5}$', message="Le code postal doit contenir 5 chiffres")]
    )

    def __str__(self):
        return self.nom

    def get_absolute_url(self):
        return reverse('centre-detail', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = "Centre"
        verbose_name_plural = "Centres"
        ordering = ['nom']
        indexes = [models.Index(fields=['nom'])]

----------------------------------------------------------------------
----------------------------------------------------------------------
from django.db import models
from .base import BaseModel
from .formations import Formation
from .utilisateurs import Utilisateur


class Commentaire(BaseModel):
    """Commentaires sur les formations"""
    formation = models.ForeignKey(
        Formation, 
        on_delete=models.CASCADE, 
        related_name="commentaires", 
        verbose_name="Formation"
    )
    auteur = models.CharField(max_length=255, verbose_name="Auteur du commentaire", blank=True)
    contenu = models.TextField(verbose_name="Contenu du commentaire")
    utilisateur = models.ForeignKey(
        Utilisateur, 
        on_delete=models.CASCADE, 
        related_name="commentaires", 
        verbose_name="Utilisateur associé"
    )

    def __str__(self):
        return f"Commentaire de {self.utilisateur} pour la formation {self.formation.nom}"
    
    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        ordering = ['-created_at']

----------------------------------------------------------------------
----------------------------------------------------------------------
from django.db import models
from .base import BaseModel
from .formations import Formation


class Document(BaseModel):
    """Documents liés aux formations"""
    formation = models.ForeignKey(
        Formation, 
        on_delete=models.CASCADE, 
        related_name="documents", 
        verbose_name="Formation associée"
    )
    nom_fichier = models.CharField(max_length=255, verbose_name="Nom du fichier")
    fichier = models.FileField(upload_to='formations/documents/', verbose_name="Fichier")
    source = models.TextField(null=True, blank=True, verbose_name="Source du document")

    def __str__(self):
        return self.nom_fichier

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-created_at']

----------------------------------------------------------------------
----------------------------------------------------------------------
from django.db import models
from django.core.exceptions import ValidationError
from .base import BaseModel
from .formations import Formation
from .ressources import Ressource


class Evenement(BaseModel):
    """Événements liés aux formations"""
    # Constantes pour les types d'événements
    INFO_PRESENTIEL = 'info_collective_presentiel'
    INFO_DISTANCIEL = 'info_collective_distanciel'
    JOB_DATING = 'job_dating'
    EVENEMENT_EMPLOI = 'evenement_emploi'
    FORUM = 'forum'
    JPO = 'jpo'
    AUTRE = 'autre'
    
    TYPE_EVENEMENT_CHOICES = [
        (INFO_PRESENTIEL, 'Information collective présentiel'),
        (INFO_DISTANCIEL, 'Information collective distanciel'),
        (JOB_DATING, 'Job dating'),
        (EVENEMENT_EMPLOI, 'Événement emploi'),
        (FORUM, 'Forum'),
        (JPO, 'JPO'),
        (AUTRE, 'Autre'),
    ]

    formation = models.ForeignKey(
        Formation, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name="evenements"
    )
    type_evenement = models.CharField(max_length=100, choices=TYPE_EVENEMENT_CHOICES, verbose_name="Type d'événement")
    details = models.TextField(null=True, blank=True, verbose_name="Détails de l'événement")
    event_date = models.DateField(verbose_name="Date de l'événement")
    description_autre = models.CharField(
        max_length=255, 
        null=True, 
        blank=True, 
        verbose_name="Description de l'autre événement"
    )

    def clean(self):
        """Validation personnalisée pour les événements de type 'autre'"""
        if self.type_evenement == self.AUTRE and not self.description_autre:
            raise ValidationError({
                'description_autre': "Veuillez fournir une description pour l'événement 'Autre'."
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Mettre à jour le nombre d'événements dans Ressource si c'est un nouvel événement
        if is_new and self.formation:
            ressource, created = Ressource.objects.get_or_create(formation=self.formation)
            ressource.nombre_evenements = Evenement.objects.filter(formation=self.formation).count()
            ressource.save(update_fields=['nombre_evenements', 'updated_at'])

    class Meta:
        verbose_name = "Événement"
        verbose_name_plural = "Événements"
        ordering = ['-event_date']
        indexes = [models.Index(fields=['event_date'])]

    def __str__(self):
        return f"{self.get_type_evenement_display()} - {self.event_date}"

----------------------------------------------------------------------
----------------------------------------------------------------------
from django.db import models
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from .centres import Centre
from .types_offre import TypeOffre
from .base import BaseModel
from .statut import Statut


class FormationManager(models.Manager):
    """Manager personnalisé pour le modèle Formation"""
    def formations_actives(self):
        """Récupère les formations actives (non terminées)"""
        return self.filter(
            models.Q(end_date__gt=timezone.now()) | 
            models.Q(end_date__isnull=True)
        )
    
    def formations_a_venir(self):
        """Récupère les formations à venir"""
        return self.filter(start_date__gt=timezone.now())
    
    def formations_terminees(self):
        """Récupère les formations terminées"""
        return self.filter(end_date__lt=timezone.now())


class Formation(BaseModel):
    """Modèle principal des formations"""
    nom = models.CharField(max_length=255, verbose_name="Nom de la formation")
    centre = models.ForeignKey(
        Centre, 
        on_delete=models.CASCADE, 
        related_name='formations', 
        verbose_name="Centre de formation"
    )
    type_offre = models.ForeignKey(
        TypeOffre, 
        on_delete=models.CASCADE, 
        related_name="formations", 
        verbose_name="Type d'offre"
    )
    statut = models.ForeignKey(
        Statut, 
        on_delete=models.CASCADE, 
        related_name="formations", 
        verbose_name="Statut de la formation"
    )
    start_date = models.DateField(null=True, blank=True, verbose_name="Date de début")
    end_date = models.DateField(null=True, blank=True, verbose_name="Date de fin")
    num_kairos = models.CharField(max_length=50, null=True, blank=True, verbose_name="Numéro Kairos")
    num_offre = models.CharField(max_length=50, null=True, blank=True, verbose_name="Numéro de l'offre")
    num_produit = models.CharField(max_length=50, null=True, blank=True, verbose_name="Numéro du produit")
    prevus_crif = models.PositiveIntegerField(verbose_name="Prévus CRIF", default=0)
    prevus_mp = models.PositiveIntegerField(verbose_name="Prévus MP", default=0)
    inscrits_crif = models.PositiveIntegerField(default=0, verbose_name="Inscrits CRIF")
    inscrits_mp = models.PositiveIntegerField(default=0, verbose_name="Inscrits MP")
    assistante = models.CharField(max_length=255, null=True, blank=True, verbose_name="Assistante responsable")
    cap = models.PositiveIntegerField(null=True, blank=True, verbose_name="Capacité maximum")
    convocation_envoie = models.BooleanField(default=False, verbose_name="Convocation envoyée")
    entresformation = models.PositiveIntegerField(default=0, verbose_name="Entrées en formation")
    
    # Utilisation du manager personnalisé
    objects = FormationManager()
    
    @property
    def total_places(self):
        """Calcule le nombre total de places"""
        return self.prevus_crif + self.prevus_mp
    
    @property
    def inscrits_total(self):
        """Calcule le nombre total d'inscrits"""
        return self.inscrits_crif + self.inscrits_mp
    
    @property
    def a_recruter(self):
        """Calcule le nombre de personnes à recruter"""
        return max(0, self.total_places - self.inscrits_total)
    
    @property
    def taux_remplissage(self):
        """Calcule le taux de remplissage"""
        if self.total_places > 0:
            return (self.inscrits_total / self.total_places) * 100
        return 0
    
    @property
    def est_active(self):
        """Vérifie si la formation est active"""
        return not self.end_date or self.end_date >= timezone.now().date()
    
    def clean(self):
        """Validation personnalisée pour les dates"""
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError({
                'end_date': "La date de fin ne peut pas être antérieure à la date de début."
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('formation-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Formation"
        verbose_name_plural = "Formations"
        ordering = ['-start_date', 'nom']
        indexes = [
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
            models.Index(fields=['nom']),
        ]

----------------------------------------------------------------------
----------------------------------------------------------------------
from django.db import models
from .base import BaseModel
from .formations import Formation
from .utilisateurs import Utilisateur


class HistoriqueFormation(BaseModel):
    """Historique des modifications de formations"""
    formation = models.ForeignKey(
        Formation, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name="historique_formations"
    )
    utilisateur = models.ForeignKey(
        Utilisateur, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="historique_utilisateurs"
    )
    action = models.CharField(max_length=255)
    ancien_statut = models.CharField(max_length=100, null=True, blank=True)
    nouveau_statut = models.CharField(max_length=100, null=True, blank=True)
    details = models.JSONField(null=True, blank=True)
    
    # Champs pour le suivi statistique
    inscrits_total = models.PositiveIntegerField(null=True, blank=True, verbose_name="Nombre d'inscrits total")
    inscrits_crif = models.PositiveIntegerField(null=True, blank=True, verbose_name="Nombre d'inscrits CRIF")
    inscrits_mp = models.PositiveIntegerField(null=True, blank=True, verbose_name="Nombre d'inscrits MP")
    total_places = models.PositiveIntegerField(null=True, blank=True, verbose_name="Nombre total de places")
    
    # Période de l'évolution
    semaine = models.PositiveIntegerField(null=True, blank=True, verbose_name="Semaine")
    mois = models.PositiveIntegerField(null=True, blank=True, verbose_name="Mois")
    annee = models.PositiveIntegerField(null=True, blank=True, verbose_name="Année")
    
    @property
    def taux_remplissage(self):
        """Calcule le taux de remplissage"""
        if self.total_places and self.total_places > 0 and self.inscrits_total is not None:
            return (self.inscrits_total / self.total_places) * 100
        return 0
    
    class Meta:
        verbose_name = "Historique de la formation"
        verbose_name_plural = "Historiques des formations"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f"{self.formation.nom if self.formation else 'Formation inconnue'} - {self.created_at.strftime('%Y-%m-%d')}"

----------------------------------------------------------------------
----------------------------------------------------------------------
from django.db import models
from .base import BaseModel


class Parametre(BaseModel):
    """Paramètres généraux de l'application"""
    cle = models.CharField(max_length=100, unique=True)
    valeur = models.TextField()
    description = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return self.cle

    class Meta:
        verbose_name = "Paramètre"
        verbose_name_plural = "Paramètres"
        ordering = ['cle']

----------------------------------------------------------------------
----------------------------------------------------------------------
from django.db import models
from django.core.exceptions import ValidationError
from .base import BaseModel
from .formations import Formation


class Rapport(BaseModel):
    """Rapports périodiques sur les formations"""
    HEBDOMADAIRE = 'Hebdomadaire'
    MENSUEL = 'Mensuel'
    ANNUEL = 'Annuel'
    
    PERIODE_CHOICES = [
        (HEBDOMADAIRE, 'Hebdomadaire'),
        (MENSUEL, 'Mensuel'),
        (ANNUEL, 'Annuel'),
    ]
    
    formation = models.ForeignKey(
        Formation, 
        on_delete=models.CASCADE, 
        related_name="rapports", 
        null=True, 
        blank=True
    )
    periode = models.CharField(max_length=50, choices=PERIODE_CHOICES, verbose_name="Période du rapport")
    date_debut = models.DateField(verbose_name="Date de début de la période")
    date_fin = models.DateField(verbose_name="Date de fin de la période")
    total_inscrits = models.PositiveIntegerField(verbose_name="Total des inscrits", default=0)
    inscrits_crif = models.PositiveIntegerField(verbose_name="Inscrits CRIF", default=0)
    inscrits_mp = models.PositiveIntegerField(verbose_name="Inscrits MP", default=0)
    total_places = models.PositiveIntegerField(verbose_name="Total des places", default=0)
    nombre_evenements = models.PositiveIntegerField(verbose_name="Nombre d'événements", default=0)
    nombre_candidats = models.PositiveIntegerField(verbose_name="Nombre de candidats", default=0)
    nombre_entretiens = models.PositiveIntegerField(verbose_name="Nombre d'entretiens", default=0)
    
    @property
    def taux_remplissage(self):
        """Calcule le taux de remplissage"""
        if self.total_places > 0:
            return (self.total_inscrits / self.total_places) * 100
        return 0
    
    @property
    def taux_transformation(self):
        """Calcule le taux de transformation"""
        if self.nombre_candidats > 0:
            return (self.total_inscrits / self.nombre_candidats) * 100
        return 0
    
    def clean(self):
        """Validation personnalisée pour les dates"""
        if self.date_debut > self.date_fin:
            raise ValidationError({
                'date_fin': "La date de fin ne peut pas être antérieure à la date de début."
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Rapport de formation"
        verbose_name_plural = "Rapports de formation"
        ordering = ['-date_fin']
        indexes = [
            models.Index(fields=['date_debut']),
            models.Index(fields=['date_fin']),
            models.Index(fields=['periode']),
        ]

    def __str__(self):
        return f"Rapport {self.formation.nom if self.formation else 'Global'} - {self.periode} ({self.date_debut} à {self.date_fin})"

----------------------------------------------------------------------
----------------------------------------------------------------------
from django.db import models
from django.core.exceptions import ValidationError
from .base import BaseModel
from .formations import Formation


class Rapport(BaseModel):
    """Rapports périodiques sur les formations"""
    HEBDOMADAIRE = 'Hebdomadaire'
    MENSUEL = 'Mensuel'
    ANNUEL = 'Annuel'
    
    PERIODE_CHOICES = [
        (HEBDOMADAIRE, 'Hebdomadaire'),
        (MENSUEL, 'Mensuel'),
        (ANNUEL, 'Annuel'),
    ]
    
    formation = models.ForeignKey(
        Formation, 
        on_delete=models.CASCADE, 
        related_name="rapports", 
        null=True, 
        blank=True
    )
    periode = models.CharField(max_length=50, choices=PERIODE_CHOICES, verbose_name="Période du rapport")
    date_debut = models.DateField(verbose_name="Date de début de la période")
    date_fin = models.DateField(verbose_name="Date de fin de la période")
    total_inscrits = models.PositiveIntegerField(verbose_name="Total des inscrits", default=0)
    inscrits_crif = models.PositiveIntegerField(verbose_name="Inscrits CRIF", default=0)
    inscrits_mp = models.PositiveIntegerField(verbose_name="Inscrits MP", default=0)
    total_places = models.PositiveIntegerField(verbose_name="Total des places", default=0)
    nombre_evenements = models.PositiveIntegerField(verbose_name="Nombre d'événements", default=0)
    nombre_candidats = models.PositiveIntegerField(verbose_name="Nombre de candidats", default=0)
    nombre_entretiens = models.PositiveIntegerField(verbose_name="Nombre d'entretiens", default=0)
    
    @property
    def taux_remplissage(self):
        """Calcule le taux de remplissage"""
        if self.total_places > 0:
            return (self.total_inscrits / self.total_places) * 100
        return 0
    
    @property
    def taux_transformation(self):
        """Calcule le taux de transformation"""
        if self.nombre_candidats > 0:
            return (self.total_inscrits / self.nombre_candidats) * 100
        return 0
    
    def clean(self):
        """Validation personnalisée pour les dates"""
        if self.date_debut > self.date_fin:
            raise ValidationError({
                'date_fin': "La date de fin ne peut pas être antérieure à la date de début."
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Rapport de formation"
        verbose_name_plural = "Rapports de formation"
        ordering = ['-date_fin']
        indexes = [
            models.Index(fields=['date_debut']),
            models.Index(fields=['date_fin']),
            models.Index(fields=['periode']),
        ]

    def __str__(self):
        return f"Rapport {self.formation.nom if self.formation else 'Global'} - {self.periode} ({self.date_debut} à {self.date_fin})"

----------------------------------------------------------------------
----------------------------------------------------------------------
from django.db import models

from .types_offre import TypeOffre
from .base import BaseModel
from .utilisateurs import Utilisateur
from .centres import Centre
from .statut import Statut


class Recherche(BaseModel):
    """Suivi des recherches effectuées par les utilisateurs"""
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recherches",
        verbose_name="Utilisateur"
    )
    terme_recherche = models.CharField(
        max_length=255, 
        verbose_name="Terme de recherche",
        null=True,
        blank=True
    )
    filtre_centre = models.ForeignKey(
        Centre,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recherches",
        verbose_name="Centre filtré"
    )
    filtre_type_offre = models.ForeignKey(
        TypeOffre,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recherches",
        verbose_name="Type d'offre filtré"
    )
    filtre_statut = models.ForeignKey(
        Statut,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recherches",
        verbose_name="Statut filtré"
    )
    date_debut = models.DateField(null=True, blank=True, verbose_name="Date de début filtrée")
    date_fin = models.DateField(null=True, blank=True, verbose_name="Date de fin filtrée")
    nombre_resultats = models.PositiveIntegerField(default=0, verbose_name="Nombre de résultats obtenus")
    temps_execution = models.FloatField(null=True, blank=True, verbose_name="Temps d'exécution (ms)")
    adresse_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="Adresse IP")
    user_agent = models.TextField(null=True, blank=True, verbose_name="User Agent")
    
    @property
    def a_trouve_resultats(self):
        """Indique si la recherche a donné des résultats"""
        return self.nombre_resultats > 0
    
    def __str__(self):
        terme = self.terme_recherche or "Sans terme"
        utilisateur = self.utilisateur or "Anonyme"
        return f"Recherche '{terme}' par {utilisateur} ({self.nombre_resultats} résultats)"
    
    class Meta:
        verbose_name = "Recherche"
        verbose_name_plural = "Recherches"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['terme_recherche']),
            models.Index(fields=['created_at']),
            models.Index(fields=['nombre_resultats']),
        ]

----------------------------------------------------------------------
----------------------------------------------------------------------
from django.db import models
from .base import BaseModel
from .formations import Formation


class Ressource(BaseModel):
    """Ressources liées aux formations"""
    formation = models.OneToOneField(
        Formation, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name="ressource"
    )
    nombre_candidats = models.PositiveIntegerField(null=True, blank=True, verbose_name="Nombre de candidats")
    nombre_entretiens = models.PositiveIntegerField(null=True, blank=True, verbose_name="Nombre d'entretiens")
    nombre_evenements = models.PositiveIntegerField(default=0, verbose_name="Nombre d'événements")
    
    @property
    def nombre_inscrits(self):
        """Récupère le nombre d'inscrits de la formation associée"""
        return self.formation.inscrits_total if self.formation else 0
    
    @property
    def taux_transformation(self):
        """Calcule le taux de transformation"""
        if self.nombre_candidats and self.nombre_candidats > 0 and self.nombre_inscrits > 0:
            return (self.nombre_inscrits / self.nombre_candidats) * 100
        return 0
    
    def __str__(self):
        return f"Ressource pour {self.formation.nom if self.formation else 'Formation inconnue'}"

    class Meta:
        verbose_name = "Ressource"
        verbose_name_plural = "Ressources"

----------------------------------------------------------------------
----------------------------------------------------------------------
from django.db import models
from django.core.exceptions import ValidationError
from .base import BaseModel


class Statut(BaseModel):
    """Statut des formations"""
    # Constantes pour les choix de statut
    NON_DEFINI = 'non_defini'
    RECRUTEMENT_EN_COURS = 'recrutement_en_cours'
    FORMATION_EN_COURS = 'formation_en_cours'
    FORMATION_A_ANNULER = 'formation_a_annuler'
    FORMATION_A_REPOUSSER = 'formation_a_repousser'
    FORMATION_ANNULEE = 'formation_annulee'
    PLEINE = 'pleine'
    QUASI_PLEINE = 'quasi_pleine'
    AUTRE = 'autre'
    
    STATUT_CHOICES = [
        (NON_DEFINI, 'Non défini'),
        (RECRUTEMENT_EN_COURS, 'Recrutement en cours'),
        (FORMATION_EN_COURS, 'Formation en cours'),
        (FORMATION_A_ANNULER, 'Formation à annuler'),
        (FORMATION_A_REPOUSSER, 'Formation à repousser'),
        (FORMATION_ANNULEE, 'Formation annulée'),
        (PLEINE, 'Pleine'),
        (QUASI_PLEINE, 'Quasi-pleine'),
        (AUTRE, 'Autre'),
    ]
    
    nom = models.CharField(max_length=100, choices=STATUT_CHOICES, verbose_name="Nom du statut")
    couleur = models.CharField(max_length=20, verbose_name="Couleur", help_text="Format: #RRGGBB ou nom de couleur")
    description_autre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Description personnalisée")
    
    def clean(self):
        """Validation personnalisée pour les statuts de type 'autre'"""
        if self.nom == self.AUTRE and not self.description_autre:
            raise ValidationError({
                'description_autre': "Le champ 'description_autre' doit être renseigné lorsque le statut est 'autre'."
            })

    def save(self, *args, **kwargs):
        self.full_clean()  # Appelle la méthode clean() avant la sauvegarde
        super().save(*args, **kwargs)

    def __str__(self):
        if self.nom == self.AUTRE and self.description_autre:
            return f"{self.description_autre} - {self.couleur}"
        return f"{self.get_nom_display()} - {self.couleur}"

    class Meta:
        verbose_name = "Statut"
        verbose_name_plural = "Statuts"
        ordering = ['nom']
----------------------------------------------------------------------
----------------------------------------------------------------------
from django.db import models
from django.core.exceptions import ValidationError
from .base import BaseModel


class TypeOffre(BaseModel):
    """Types d'offres de formation"""
    # Constantes pour les choix de types d'offre
    CRIF = 'crif'
    ALTERNANCE = 'alternance'
    POEC = 'poec'
    POEI = 'poei'
    TOSA = 'tosa'
    AUTRE = 'autre'
    NON_DEFINI = 'non_defini'
    
    TYPE_OFFRE_CHOICES = [
        (CRIF, 'CRIF'),
        (ALTERNANCE, 'Alternance'),
        (POEC, 'POEC'),
        (POEI, 'POEI'),
        (TOSA, 'TOSA'),
        (AUTRE, 'Autre'),
        (NON_DEFINI, 'Non défini'),
    ]
    
    nom = models.CharField(max_length=100, choices=TYPE_OFFRE_CHOICES, default=NON_DEFINI, verbose_name="Type d'offre")
    autre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Autre (personnalisé)")
    
    def clean(self):
        if self.nom == self.AUTRE and not self.autre:
            raise ValidationError({
                'autre': "Le champ 'autre' doit être renseigné lorsque le type d'offre est 'autre'."
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.nom == self.AUTRE and self.autre:
            return self.autre
        return self.get_nom_display()

    class Meta:
        verbose_name = "Type d'offre"
        verbose_name_plural = "Types d'offres"
        ordering = ['nom']

----------------------------------------------------------------------
----------------------------------------------------------------------
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
import uuid


class Utilisateur(AbstractUser):
    """Modèle utilisateur étendu basé sur AbstractUser de Django"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=50, blank=True, verbose_name="Rôle")
    
    # Redéfinition des relations many-to-many avec related_name personnalisé
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name='utilisateur_set',
        related_query_name='utilisateur'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='utilisateur_set',
        related_query_name='utilisateur'
    )
    
    def __str__(self):
        return f"{self.get_full_name() or self.username}"
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
----------------------------------------------------------------------
----------------------------------------------------------------------

Lancer les tests des models
python3 manage.py test rap_app.tests.test_models







les models ont des relations entre eux. une foration peut donc avoir des commentaires, des documents, des ressources associés et evenements. lorsqu'un evenement est cree, il est comptabilisé dans ressources. verifie la cohérence des models. de plus, le model formation calculte automatiquement le nombre de places totales, le nombre de places à recruter, le taux de remplissage...et bien entendu, une formation à un statut, un type d'offre, un centre. et l'utilisateurs peut utiliser des filtres pour afficher les entreprises