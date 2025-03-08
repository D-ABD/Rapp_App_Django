from django.db import models
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from .base import BaseModel
from .formations import Formation


User = get_user_model()  # Utilisation du modèle utilisateur Django


class HistoriqueFormation(BaseModel):
    """
    Modèle représentant l'historique des modifications d'une formation.

    Permet de suivre :
    - Les modifications de statut
    - L'évolution des inscriptions
    - L'utilisateur ayant effectué l'action
    - La saturation au moment de la modification
    """

    formation = models.ForeignKey(
        Formation, on_delete=models.CASCADE, null=True, blank=True, 
        related_name="historique_formations", verbose_name="Formation concernée"
    )

    utilisateur = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, 
        related_name="historique_utilisateurs", verbose_name="Utilisateur ayant modifié"
    )

    action = models.CharField(max_length=255, verbose_name="Action effectuée")
    """Exemples : 'modification', 'suppression', 'ajout'."""

    ancien_statut = models.CharField(max_length=100, null=True, blank=True, verbose_name="Statut avant modification")
    nouveau_statut = models.CharField(max_length=100, null=True, blank=True, verbose_name="Statut après modification")

    details = models.JSONField(null=True, blank=True, verbose_name="Détails des modifications")
    """Stocke les modifications sous forme de JSON. Ex: {"ancien_nom": "A", "nouveau_nom": "B"}."""

    # 🔹 Gestion des inscriptions et de la saturation
    inscrits_total = models.PositiveIntegerField(null=True, blank=True, verbose_name="Total inscrits")
    inscrits_crif = models.PositiveIntegerField(null=True, blank=True, verbose_name="Inscrits CRIF")
    inscrits_mp = models.PositiveIntegerField(null=True, blank=True, verbose_name="Inscrits MP")
    total_places = models.PositiveIntegerField(null=True, blank=True, verbose_name="Total places")
    saturation = models.FloatField(null=True, blank=True, verbose_name="Niveau de saturation (%)")

    # 🔹 Taux de remplissage stocké en base de données
    taux_remplissage = models.FloatField(null=True, blank=True, verbose_name="Taux de remplissage (%)")

    # 🔹 Suivi temporel
    semaine = models.PositiveIntegerField(null=True, blank=True, verbose_name="Numéro de la semaine")
    mois = models.PositiveIntegerField(null=True, blank=True, verbose_name="Mois")
    annee = models.PositiveIntegerField(null=True, blank=True, verbose_name="Année")

    def save(self, *args, **kwargs):
        """
        Personnalisation de la sauvegarde :
        - Récupère la saturation de la formation et la stocke dans `saturation`.
        - Calcule le taux de remplissage automatiquement.
        - Remplit `semaine`, `mois`, `annee` si non fournis.
        """

        if self.formation:
            # Récupérer les valeurs de la formation associée
            self.total_places = self.formation.total_places
            self.inscrits_total = self.formation.total_inscrits
            self.inscrits_crif = self.formation.inscrits_crif
            self.inscrits_mp = self.formation.inscrits_mp
            self.saturation = self.formation.saturation  # ✅ Stocke la saturation de la formation

        if self.total_places and self.total_places > 0 and self.inscrits_total is not None:
            self.taux_remplissage = (self.inscrits_total / self.total_places) * 100
        else:
            self.taux_remplissage = 0

        if not self.semaine:
            self.semaine = self.created_at.isocalendar()[1]  # Numéro de semaine
        if not self.mois:
            self.mois = self.created_at.month  # Mois (1-12)
        if not self.annee:
            self.annee = self.created_at.year  # Année

        super().save(*args, **kwargs)  # Sauvegarde standard Django

    class Meta:
        verbose_name = "Historique de formation"
        verbose_name_plural = "Historiques des formations"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),  # Optimisation des requêtes temporelles
            models.Index(fields=['action']),  # Optimisation des recherches par action
            models.Index(fields=['formation']),  # Optimisation des recherches par formation
        ]

    def __str__(self):
        """Retourne une description lisible de l'historique."""
        return f"{self.formation.nom if self.formation else 'Formation inconnue'} - {self.created_at.strftime('%Y-%m-%d')}"
