from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from .entreprises import Entreprise
from .centres import Centre
from .types_offre import TypeOffre
from .base import BaseModel
from .statut import Statut
User = get_user_model()  # Récupère le modèle User


class FormationManager(models.Manager):
    """
    Manager personnalisé pour les requêtes sur les formations.
    Fournit des méthodes supplémentaires pour récupérer des formations selon leur statut.
    """

    def formations_actives(self):
        """Retourne uniquement les formations actives (date de fin future ou sans date de fin)."""
        return self.filter(models.Q(end_date__gt=timezone.now()) | models.Q(end_date__isnull=True))

    def formations_a_venir(self):
        """Retourne uniquement les formations qui commencent dans le futur."""
        return self.filter(start_date__gt=timezone.now())

    def formations_terminees(self):
        """Retourne uniquement les formations qui sont terminées (date de fin dépassée)."""
        return self.filter(end_date__lt=timezone.now())

    def formations_toutes(self):
        """Retourne **toutes** les formations, sans filtre."""
        return self.all()

    def formations_a_recruter(self):
        """
        Retourne uniquement les formations qui ont encore des places à pourvoir (`a_recruter > 0`).
        Utilisation de `annotate` pour effectuer le calcul dans la requête SQL, ce qui est plus efficace.
        """
        return self.annotate(
            total_places=models.F('prevus_crif') + models.F('prevus_mp'),
            total_inscrits=models.F('inscrits_crif') + models.F('inscrits_mp')
        ).filter(total_places__gt=models.F('total_inscrits'))

    def trier_par(self, champ_tri):
        """Trie les formations selon un champ donné, si autorisé."""
        champs_autorises = [
            "centre", "-centre",
            "statut", "-statut",
            "type_offre", "-type_offre",
            "start_date", "-start_date",
            "end_date", "-end_date"
        ]
        return self.get_queryset().order_by(champ_tri) if champ_tri in champs_autorises else self.get_queryset()

    def formations_par_entreprise(self, entreprise_id):
        """Retourne les formations associées à une entreprise spécifique via la relation ManyToMany."""
        return self.filter(entreprises__id=entreprise_id)


class Formation(BaseModel):
    """
    Modèle représentant une formation.
    Hérite de `BaseModel`, qui contient les champs `created_at` et `updated_at` pour la gestion des dates.
    """

    # Informations générales
    nom = models.CharField(max_length=255, verbose_name="Nom de la formation")
    centre = models.ForeignKey(Centre, on_delete=models.CASCADE, related_name='formations', verbose_name="Centre de formation")
    type_offre = models.ForeignKey(TypeOffre, on_delete=models.CASCADE, related_name="formations", verbose_name="Type d'offre")
    statut = models.ForeignKey(Statut, on_delete=models.CASCADE, related_name="formations", verbose_name="Statut de la formation")

    # Dates et identifiants
    start_date = models.DateField(null=True, blank=True, verbose_name="Date de début")
    end_date = models.DateField(null=True, blank=True, verbose_name="Date de fin")
    num_kairos = models.CharField(max_length=50, null=True, blank=True, verbose_name="Numéro Kairos")
    num_offre = models.CharField(max_length=50, null=True, blank=True, verbose_name="Numéro de l'offre")
    num_produit = models.CharField(max_length=50, null=True, blank=True, verbose_name="Numéro du produit")

    # Gestion des places et des inscriptions
    prevus_crif = models.PositiveIntegerField(default=0, verbose_name="Prévus CRIF")
    prevus_mp = models.PositiveIntegerField(default=0, verbose_name="Prévus MP")
    inscrits_crif = models.PositiveIntegerField(default=0, verbose_name="Inscrits CRIF")
    inscrits_mp = models.PositiveIntegerField(default=0, verbose_name="Inscrits MP")
    saturation = models.FloatField(null=True, blank=True, verbose_name="Taux de saturation (%)")

    # Informations supplémentaires
    assistante = models.CharField(max_length=255, null=True, blank=True, verbose_name="Assistante responsable")
    cap = models.PositiveIntegerField(null=True, blank=True, verbose_name="Capacité maximum")
    convocation_envoie = models.BooleanField(default=False, verbose_name="Convocation envoyée")
    entresformation = models.PositiveIntegerField(default=0, verbose_name="Entrées en formation")

    # Statistiques de recrutement
    nombre_candidats = models.PositiveIntegerField(default=0, verbose_name="Nombre de candidats")
    nombre_entretiens = models.PositiveIntegerField(default=0, verbose_name="Nombre d'entretiens")

    # Nombre d'événements liés
    nombre_evenements = models.PositiveIntegerField(default=0, verbose_name="Nombre d'événements")

    # Informations sur les commentaires et la saturation
    dernier_commentaire = models.TextField(null=True, blank=True, verbose_name="Dernier commentaire")

    # Relation ManyToMany avec Entreprise
    entreprises = models.ManyToManyField(Entreprise, related_name="formations", verbose_name="Entreprises associées", blank=True)

    utilisateur = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="formations_creees",  # ✅ Change ici pour éviter un conflit
        verbose_name="Créé par"
    )
    # Manager personnalisé
    objects = FormationManager()

    def get_absolute_url(self):
        """Retourne l'URL de détail de la formation."""
        return reverse('formation-detail', kwargs={'pk': self.pk})
    
    def get_commentaires(self):
        """Retourne tous les commentaires associés à cette formation."""
        return self.commentaires.all()
    
    def get_evenements(self):
        """Retourne tous les événements associés à cette formation."""
        return self.evenements.all()
    
    # 🔍 Ajout d'un accès rapide aux événements par type
    def get_nombre_evenements_par_type(self):
        """Retourne un dictionnaire contenant le nombre d'événements par type pour cette formation."""
        evenements_par_type = (
            self.evenements.values("type_evenement")
            .annotate(total=models.Count("type_evenement"))
            .order_by()  # ✅ Conserve l'ordre sans doublons
    )
        return {e["type_evenement"]: e["total"] for e in evenements_par_type}


    
    # 🔍 Récupérer tous les documents liés à la formation
    def get_documents(self):
        """
        Retourne tous les documents associés à cette formation.
        """
        return self.documents.all()


    @property
    def is_a_recruter(self):
        """Renvoie `True` si la formation a encore des places disponibles, sinon `False`."""
        return self.a_recruter > 0

    
    @property
    def total_places(self):
        """Retourne le nombre total de places prévues (CRIF + MP)."""
        return (self.prevus_crif or 0) + (self.prevus_mp or 0)

    @property
    def total_inscrits(self):
        """Retourne le nombre total d'inscrits (CRIF + MP)."""
        return (self.inscrits_crif or 0) + (self.inscrits_mp or 0)

    @property
    def a_recruter(self):
        """Calcule le nombre de places encore disponibles pour la formation."""
        return max(0, self.total_places - self.total_inscrits)  # Évite les valeurs négatives


    class Meta:
        verbose_name = "Formation"
        verbose_name_plural = "Formations"
        ordering = ['-start_date', 'nom']
        indexes = [
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
            models.Index(fields=['nom']),
        ]

    def __str__(self):
        """Retourne une représentation textuelle de la formation."""
        return f"{self.nom} ({self.centre.nom if self.centre else 'Centre inconnu'})"
    
    def save(self, *args, **kwargs):
        """Mise à jour automatique de la saturation lors de la sauvegarde."""
        # Calcul de la saturation avant la sauvegarde
        if self.total_places > 0:
            self.saturation = (self.total_inscrits / self.total_places) * 100
        else:
            self.saturation = 0
            
        # Une seule sauvegarde avec toutes les modifications
        super().save(*args, **kwargs)