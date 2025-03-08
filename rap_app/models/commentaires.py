from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .base import BaseModel
from .formations import Formation
from django.contrib.auth import get_user_model
User = get_user_model()


class Commentaire(BaseModel):
    """
    Modèle représentant un commentaire associé à une formation.
    """

    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name="commentaires", verbose_name="Formation")
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name="commentaires", verbose_name="Utilisateur associé")
    contenu = models.TextField(verbose_name="Contenu du commentaire")
    saturation = models.PositiveIntegerField(null=True, blank=True,verbose_name="Niveau de saturation (%)")

    def __str__(self):
        """
        Retourne une représentation lisible du commentaire.
        """
        return f"Commentaire de {self.utilisateur} sur {self.formation.nom} ({self.created_at.strftime('%d/%m/%Y')})"

    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        ordering = ['formation', '-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['formation']),
        ]


@receiver(post_save, sender=Commentaire)
def update_formation_saturation(sender, instance, **kwargs):
    """
    Met à jour la `saturation` de la formation avec la dernière valeur de saturation du commentaire.
    Met également à jour le `dernier_commentaire` pour un affichage rapide.
    """
    if instance.formation:
        # Mise à jour directe via update() pour court-circuiter les méthodes save()
        updates = {}
        
        if instance.saturation is not None:
            updates['saturation'] = instance.saturation
        
        # Récupérer le dernier commentaire
        dernier_commentaire = Commentaire.objects.filter(formation=instance.formation).order_by('-created_at').first()
        updates['dernier_commentaire'] = dernier_commentaire.contenu if dernier_commentaire else None
        
        # Appliquer toutes les mises à jour en une seule opération
        if updates:
            Formation.objects.filter(id=instance.formation.id).update(**updates)

@receiver(post_delete, sender=Commentaire)
def handle_commentaire_delete(sender, instance, **kwargs):
    """
    Met à jour la formation après la suppression d'un commentaire :
    - Met à jour le `dernier_commentaire` avec le commentaire précédent s'il en reste un.
    """
    if instance.formation:
        # Récupérer directement le dernier commentaire à partir du modèle
        dernier_commentaire = Commentaire.objects.filter(formation=instance.formation).order_by('-created_at').first()
        Formation.objects.filter(id=instance.formation.id).update(
            dernier_commentaire=dernier_commentaire.contenu if dernier_commentaire else None
        )