from django.db import models
from .base import BaseModel

class Entreprise(BaseModel):
    """
    Modèle représentant une entreprise.

    Ajout d'une relation avec `Formation` pour que les entreprises puissent être utilisées comme ressources.
    """

    nom = models.CharField(max_length=255, verbose_name="Nom de l'entreprise", unique=True )
    secteur_activite = models.CharField(max_length=255, verbose_name="Secteur d'activité",blank=True,null=True)
    contact_nom = models.CharField(max_length=255,verbose_name="Nom du contact",blank=True,null=True)
    contact_poste = models.CharField(max_length=255,verbose_name="Poste du contact",blank=True,null=True)
    contact_telephone = models.CharField(max_length=20, verbose_name="Téléphone du contact", blank=True, null=True)
    contact_email = models.EmailField(verbose_name="Email du contact", blank=True, null=True)
    description = models.TextField(verbose_name="Description de la relation", blank=True, null=True)

    # Manager par défaut (si EntrepriseManager est supprimé)
    objects = models.Manager()

    def __str__(self):
        """Représentation lisible de l'entreprise."""
        return self.nom

    class Meta:
        verbose_name = "Entreprise"
        verbose_name_plural = "Entreprises"
        ordering = ['nom']
        indexes = [
            models.Index(fields=['nom']),  # Index pour optimiser la recherche par nom.
        ]
