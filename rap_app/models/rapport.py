# models/rapport.py
from django.db import models
from django.core.exceptions import ValidationError
from .base import BaseModel
from .formations import Formation


class Rapport(BaseModel):
    """
    Modèle représentant un rapport périodique sur les formations.

    Ce modèle permet de suivre les performances et indicateurs clés des formations 
    sur différentes périodes : hebdomadaire, mensuelle ou annuelle.

    Hérite de `BaseModel`, qui ajoute automatiquement :
    - `created_at` : Date et heure de création du rapport.
    - `updated_at` : Date et heure de la dernière modification.
    """

    # Définition des périodes de rapport disponibles
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
        blank=True,
        verbose_name="Formation associée"
    )
    """
    Formation concernée par le rapport.
    Peut être `null` si le rapport est global et concerne toutes les formations.
    """

    periode = models.CharField(
        max_length=50, 
        choices=PERIODE_CHOICES, 
        verbose_name="Période du rapport"
    )
    """
    Indique la période du rapport :
    - 'Hebdomadaire'
    - 'Mensuel'
    - 'Annuel'
    """

    date_debut = models.DateField(verbose_name="Date de début de la période")
    """
    Début de la période couverte par le rapport.
    """

    date_fin = models.DateField(verbose_name="Date de fin de la période")
    """
    Fin de la période couverte par le rapport.
    Doit être postérieure à `date_debut`.
    """

    # Indicateurs de suivi
    total_inscrits = models.PositiveIntegerField(default=0, verbose_name="Total des inscrits")
    """
    Nombre total d'inscrits sur la période.
    """

    inscrits_crif = models.PositiveIntegerField(default=0, verbose_name="Inscrits CRIF")
    """
    Nombre d'inscrits provenant du CRIF.
    """

    inscrits_mp = models.PositiveIntegerField(default=0, verbose_name="Inscrits MP")
    """
    Nombre d'inscrits provenant du marché privé.
    """

    total_places = models.PositiveIntegerField(default=0, verbose_name="Total des places")
    """
    Nombre total de places disponibles pour la formation durant la période.
    """

    nombre_evenements = models.PositiveIntegerField(default=0, verbose_name="Nombre d'événements")
    """
    Nombre d'événements liés à la formation durant la période.
    """

    nombre_candidats = models.PositiveIntegerField(default=0, verbose_name="Nombre de candidats")
    """
    Nombre total de candidats ayant postulé à la formation sur la période.
    """

    nombre_entretiens = models.PositiveIntegerField(default=0, verbose_name="Nombre d'entretiens")
    """
    Nombre d'entretiens réalisés durant la période.
    """

    @property
    def taux_remplissage(self):
        """
        Calcule le taux de remplissage de la formation durant la période.

        Formule :
        (Nombre d'inscrits / Nombre total de places) * 100

        Retourne 0 si `total_places` est nul pour éviter une division par zéro.
        """
        if self.total_places > 0:
            return (self.total_inscrits / self.total_places) * 100
        return 0

    @property
    def taux_transformation(self):
        """
        Calcule le taux de transformation des candidats en inscrits.

        Formule :
        (Nombre d'inscrits / Nombre total de candidats) * 100

        Retourne 0 si `nombre_candidats` est nul pour éviter une division par zéro.
        """
        if self.nombre_candidats > 0:
            return (self.total_inscrits / self.nombre_candidats) * 100
        return 0

    def clean(self):
        """
        Validation personnalisée pour les dates.

        Vérifie que la date de fin est bien postérieure à la date de début.
        """
        if self.date_debut > self.date_fin:
            raise ValidationError({
                'date_fin': "La date de fin ne peut pas être antérieure à la date de début."
            })

    def save(self, *args, **kwargs):
        """
        Avant d'enregistrer, applique les validations et nettoie les données.
        """
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
    """
    - Trie les rapports par date de fin (les plus récents en premier).
    - Ajoute des index pour optimiser les requêtes sur les dates et les périodes.
    """

    def __str__(self):
        """
        Représentation textuelle du rapport.
        Affiche le nom de la formation et la période concernée.
        """
        return f"Rapport {self.formation.nom if self.formation else 'Global'} - {self.periode} ({self.date_debut} à {self.date_fin})"
