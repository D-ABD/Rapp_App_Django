# models/centres.py
from django.db import models
from django.core.validators import RegexValidator
from django.urls import reverse
from .base import BaseModel


class Centre(BaseModel):
    """
    Modèle représentant un centre de formation.

    Hérite de `BaseModel` qui ajoute les champs :
    - `created_at` : Date et heure de création de l'enregistrement.
    - `updated_at` : Date et heure de la dernière modification.

    Champs spécifiques :
    - `nom` : Nom du centre de formation (obligatoire et unique).
    - `code_postal` : Code postal du centre (optionnel).
      * Doit contenir exactement 5 chiffres (validation par regex).
    
    Méthodes :
    - `__str__` : Retourne le nom du centre.
    - `get_absolute_url` : Retourne l'URL du détail du centre.
    - `full_address` : Retourne l'adresse complète (utile pour affichage futur).

    Options du modèle :
    - `verbose_name` : Nom affiché au singulier dans l'interface d'administration.
    - `verbose_name_plural` : Nom affiché au pluriel dans l'interface d'administration.
    - `ordering` : Trie les centres par nom par défaut.
    - `indexes` : Ajoute des index sur `nom` et `code_postal` pour optimiser les recherches.
    """

    nom = models.CharField(
        max_length=255,
        unique=True,  # 🔹 Garantit qu'un centre a un nom unique
        verbose_name="Nom du centre"
    )

    code_postal = models.CharField(
        max_length=5,  # 🔹 Limité à 5 caractères au lieu de 10
        null=True,
        blank=True,
        verbose_name="Code postal",
        validators=[
            RegexValidator(
                regex=r'^\d{5}$',
                message="Le code postal doit contenir exactement 5 chiffres"
            )
        ]
    )

    def __str__(self):
        """Retourne le nom du centre pour une meilleure lisibilité."""
        return self.nom

    def get_absolute_url(self):
        """
        Retourne l'URL du détail du centre.
        Utile pour les vues génériques et les redirections après une création/modification.
        """
        return reverse('centre-detail', kwargs={'pk': self.pk})

    def full_address(self):
        """
        Retourne une version complète de l'adresse (utile si d'autres champs d'adresse sont ajoutés).
        Exemple d'usage : affichage dans une liste ou recherche avancée.
        """
        return f"{self.nom} ({self.code_postal})" if self.code_postal else self.nom

    class Meta:
        verbose_name = "Centre"
        verbose_name_plural = "Centres"
        ordering = ['nom']
        indexes = [
            models.Index(fields=['nom']),  # 🔹 Index pour optimiser les recherches par nom
            models.Index(fields=['code_postal']),  # 🔹 Index pour les recherches par code postal
        ]
