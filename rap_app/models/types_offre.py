# models/types_offre.py
from django.db import models
from django.core.exceptions import ValidationError
from .base import BaseModel


class TypeOffre(BaseModel):
    """
    Modèle représentant les types d'offres de formation.

    Ce modèle définit les différents types d'offres disponibles dans l'application, 
    comme CRIF, Alternance, POEC, POEI, etc. Il permet également d'ajouter un type personnalisé 
    via l'option "Autre".

    ✅ Utilisation principale :
    - Associer un type d'offre à une formation.
    - Filtrer les formations par type d'offre.
    - Permettre l'ajout d'un type personnalisé si besoin.
    """

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
    
    nom = models.CharField(
        max_length=100, 
        choices=TYPE_OFFRE_CHOICES, 
        default=NON_DEFINI, 
        verbose_name="Type d'offre"
    )
    """
    Nom du type d'offre, avec une liste de choix prédéfinis.
    """

    autre = models.CharField(
        max_length=255, 
        blank=True,  # Suppression de null=True pour éviter les valeurs NULL sur un CharField
        verbose_name="Autre (personnalisé)"
    )
    """
    Champ permettant de spécifier un type personnalisé si "Autre" est sélectionné.
    """

    def clean(self):
        """
        Validation personnalisée :
        - Si le type d'offre est 'Autre', alors `autre` doit être rempli.
        """
        if self.nom == self.AUTRE and not self.autre:
            raise ValidationError({
                'autre': "Le champ 'autre' doit être renseigné lorsque le type d'offre est 'autre'."
            })

    def save(self, *args, **kwargs):
        """
        Sauvegarde avec validation :
        - Appelle `clean()` avant l'enregistrement en base de données.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        """
        Représentation textuelle du modèle dans l'admin Django et les logs.
        """
        return self.autre if self.nom == self.AUTRE and self.autre else self.get_nom_display()
    
    def is_personnalise(self):
        """
        Vérifie si le type d'offre est personnalisé (Autre).
        """
        return self.nom == self.AUTRE

    class Meta:
        verbose_name = "Type d'offre"
        verbose_name_plural = "Types d'offres"
        ordering = ['nom']
        constraints = [
            models.UniqueConstraint(
                fields=['autre'],
                name='unique_autre_non_null',
                condition=models.Q(nom='autre', autre__isnull=False)
            )
        ]  # Empêche d'avoir plusieurs fois la même valeur personnalisée 'Autre'
