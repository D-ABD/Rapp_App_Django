from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import F
from .base import BaseModel
from .formations import Formation

class Evenement(BaseModel):
    """
    Modèle représentant un événement lié à une formation.
    """

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
        (JPO, 'Journée Portes Ouvertes (JPO)'),
        (AUTRE, 'Autre'),
    ]

    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, null=True, blank=True,  related_name="evenements",verbose_name="Formation associée")
    type_evenement = models.CharField(max_length=100, choices=TYPE_EVENEMENT_CHOICES, verbose_name="Type d'événement",db_index=True)
    details = models.TextField(null=True,  blank=True, verbose_name="Détails de l'événement")
    event_date = models.DateField(null=True, blank=True, verbose_name="Date de l'événement")
    description_autre = models.CharField(max_length=255,  null=True,  blank=True,  verbose_name="Description pour 'Autre' événement")

    def clean(self):
        """
        Validation personnalisée :
        - Si l'événement est de type "Autre", la description doit être remplie.
        """
        if self.type_evenement == self.AUTRE and not self.description_autre:
            raise ValidationError({
                'description_autre': "Veuillez fournir une description pour l'événement de type 'Autre'."
            })

    def save(self, *args, **kwargs):
        """
        Personnalisation de la sauvegarde :
        - Vérifie les règles de validation (`full_clean()`).
        """
        self.full_clean()  # Exécute la validation avant la sauvegarde.
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Événement"
        verbose_name_plural = "Événements"
        ordering = ['-event_date']
        indexes = [
            models.Index(fields=['event_date']),  # Optimisation des recherches par date.
            models.Index(fields=['type_evenement']),  # Ajout d'un index sur le type d'événement.
        ]

    def __str__(self):
        """
        Retourne une représentation lisible de l'événement.
        Exemple : "Job dating - 2025-03-10"
        """
        type_event = self.get_type_evenement_display() if self.type_evenement else "Type inconnu"
        return f"{type_event} - {self.event_date.strftime('%d/%m/%Y')}" if self.event_date else f"{type_event} - Date inconnue"



# 🚀 Signaux pour mettre à jour `nombre_evenements` dans `Formation`
@receiver(post_save, sender=Evenement)
def update_nombre_evenements(sender, instance, **kwargs):
    """Met à jour le nombre d'événements dans la formation associée."""
    if instance.formation:
        # Recalcule le nombre total d'événements à chaque modification
        count = Evenement.objects.filter(formation=instance.formation).count()
        Formation.objects.filter(id=instance.formation.id).update(nombre_evenements=count)
        # Rafraîchir la formation
        if hasattr(instance, 'formation'):
            instance.formation.refresh_from_db()

@receiver(post_delete, sender=Evenement)
def update_nombre_evenements_after_delete(sender, instance, **kwargs):
    """Met à jour le nombre d'événements après suppression."""
    if hasattr(instance, 'formation') and instance.formation:
        # Recalcule le nombre après suppression
        count = Evenement.objects.filter(formation=instance.formation).count()
        Formation.objects.filter(id=instance.formation.id).update(nombre_evenements=count)