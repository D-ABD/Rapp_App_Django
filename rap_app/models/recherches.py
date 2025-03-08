# models/recherches.py
from django.db import models

from .types_offre import TypeOffre
from .base import BaseModel
from .centres import Centre
from .statut import Statut


class Recherche(BaseModel):
    """
    Modèle de suivi des recherches effectuées par les utilisateurs.

    Ce modèle stocke les termes de recherche, les filtres appliqués et d'autres 
    métadonnées comme l'adresse IP, le User-Agent et le nombre de résultats obtenus.
    
    Hérite de `BaseModel`, qui ajoute automatiquement :
    - `created_at` : Date et heure de création de la recherche.
    - `updated_at` : Date et heure de la dernière modification.
    """



    terme_recherche = models.CharField(
        max_length=255, 
        verbose_name="Terme de recherche",
        null=True,
        blank=True
    )
    """
    Chaîne de texte recherchée par l'utilisateur.
    Peut être vide si l'utilisateur a uniquement utilisé des filtres.
    """

    # Filtres appliqués par l'utilisateur
    filtre_centre = models.ForeignKey(
        Centre,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recherches",
        verbose_name="Centre filtré"
    )
    """
    Filtre sur un centre de formation spécifique.
    """

    filtre_type_offre = models.ForeignKey(
        TypeOffre,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recherches",
        verbose_name="Type d'offre filtré"
    )
    """
    Filtre sur un type d'offre spécifique.
    """

    filtre_statut = models.ForeignKey(
        Statut,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recherches",
        verbose_name="Statut filtré"
    )
    """
    Filtre sur un statut spécifique de formation.
    """

    # Dates utilisées comme filtres
    date_debut = models.DateField(null=True, blank=True, verbose_name="Date de début filtrée")
    """
    Date minimale pour filtrer les résultats (ex: formations commençant après cette date).
    """

    date_fin = models.DateField(null=True, blank=True, verbose_name="Date de fin filtrée")
    """
    Date maximale pour filtrer les résultats (ex: formations se terminant avant cette date).
    """

    # Informations sur les résultats de la recherche
    nombre_resultats = models.PositiveIntegerField(default=0, verbose_name="Nombre de résultats obtenus")
    """
    Nombre total de résultats obtenus après exécution de la recherche.
    """

    temps_execution = models.FloatField(null=True, blank=True, verbose_name="Temps d'exécution (ms)")
    """
    Temps d'exécution de la requête en millisecondes (utile pour optimiser les performances).
    """





    @property
    def a_trouve_resultats(self):
        """
        Indique si la recherche a retourné des résultats.

        Retourne `True` si au moins un résultat a été trouvé, sinon `False`.
        """
        return self.nombre_resultats > 0

    def __str__(self):
        """
        Représentation textuelle de la recherche pour l'affichage dans l'admin.
        """
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
    """
    - Trie les recherches par date de création (les plus récentes en premier).
    - Ajoute des index pour optimiser les recherches sur `terme_recherche`, `created_at` et `nombre_resultats`.
    """
