import datetime
from django.db import models
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from .base import BaseModel
from .formations import Formation

User = get_user_model()

class HistoriqueFormation(BaseModel):
    formation = models.ForeignKey(
        Formation, on_delete=models.CASCADE, null=True, blank=True, 
        related_name="historique_formations", verbose_name="Formation concernée"
    )
    utilisateur = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, 
        related_name="historique_utilisateurs", verbose_name="Utilisateur ayant modifié"
    )

    action = models.CharField(max_length=255, verbose_name="Action effectuée")

    ancien_statut = models.CharField(max_length=100, null=True, blank=True, verbose_name="Statut avant modification")
    nouveau_statut = models.CharField(max_length=100, null=True, blank=True, verbose_name="Statut après modification")

    details = models.JSONField(null=True, blank=True, verbose_name="Détails des modifications")

    inscrits_total = models.PositiveIntegerField(null=True, blank=True, verbose_name="Total inscrits")
    inscrits_crif = models.PositiveIntegerField(null=True, blank=True, verbose_name="Inscrits CRIF")
    inscrits_mp = models.PositiveIntegerField(null=True, blank=True, verbose_name="Inscrits MP")
    total_places = models.PositiveIntegerField(null=True, blank=True, verbose_name="Total places")
    saturation = models.FloatField(null=True, blank=True, verbose_name="Niveau de saturation (%)")
    taux_remplissage = models.FloatField(null=True, blank=True, verbose_name="Taux de remplissage (%)")

    semaine = models.PositiveIntegerField(null=True, blank=True, verbose_name="Numéro de la semaine")
    mois = models.PositiveIntegerField(null=True, blank=True, verbose_name="Mois")
    annee = models.PositiveIntegerField(null=True, blank=True, verbose_name="Année")

    def save(self, *args, **kwargs):
        """
        Personnalisation de la sauvegarde :
        - Récupère les valeurs dynamiques de la formation
        - Convertit les données avant enregistrement pour éviter les erreurs JSON
        """
        if self.formation:
            # 🔥 Calcul dynamique des valeurs issues de `Formation`
            self.total_places = (self.formation.prevus_crif or 0) + (self.formation.prevus_mp or 0)
            self.inscrits_total = (self.formation.inscrits_crif or 0) + (self.formation.inscrits_mp or 0)
            self.inscrits_crif = self.formation.inscrits_crif
            self.inscrits_mp = self.formation.inscrits_mp
            self.saturation = (self.inscrits_total / self.total_places) * 100 if self.total_places > 0 else 0
            self.taux_remplissage = (self.inscrits_total / self.total_places) * 100 if self.total_places > 0 else 0

            # ✅ Stocke les valeurs temporelles si elles ne sont pas encore définies
            if not self.semaine:
                self.semaine = self.created_at.isocalendar()[1]
            if not self.mois:
                self.mois = self.created_at.month
            if not self.annee:
                self.annee = self.created_at.year

            # ✅ Convertit toutes les données en format JSON-safe
            self.details = self._serialize_details(self.formation.to_serializable_dict())

        super().save(*args, **kwargs)

    def _serialize_details(self, details):
        """
        Convertit les objets non sérialisables (ex: dates) en chaînes de caractères JSON-compatibles.
        """
        def convert_value(value):
            if isinstance(value, (datetime.date, datetime.datetime)):
                return value.strftime('%Y-%m-%d %H:%M:%S')  # ✅ Format JSON-compatible
            return value  # Garde les autres valeurs inchangées

        return {key: convert_value(value) for key, value in details.items()}

    class Meta:
        verbose_name = "Historique de formation"
        verbose_name_plural = "Historiques des formations"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['formation']),
        ]

    def __str__(self):
        return f"{self.formation.nom if self.formation else 'Formation inconnue'} - {self.created_at.strftime('%Y-%m-%d')}"
