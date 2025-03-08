# models/parametres.py
from django.db import models
from .base import BaseModel


class Parametre(BaseModel):
    """
    Modèle représentant les paramètres généraux de l'application.

    Ce modèle permet de stocker des configurations dynamiques sans modifier directement 
    le code ou la base de données. Il est utilisé pour gérer des réglages comme :
    - Modes d'affichage (ex: mode sombre, affichage des logs).
    - Paramètres métiers (ex: nombre maximum d'inscriptions par formation).
    - Clés API ou identifiants spécifiques.

    Hérite de `BaseModel`, qui ajoute automatiquement :
    - `created_at` : Date et heure de création du paramètre.
    - `updated_at` : Date et heure de la dernière modification.
    """

    cle = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name="Clé du paramètre"
    )
    """
    Identifiant unique du paramètre.
    Exemples : 
    - 'mode_sombre' pour activer/désactiver le mode dark.
    - 'nombre_max_inscriptions' pour définir une limite d'inscriptions.
    - 'url_webhook_teams' pour configurer les notifications vers Teams.
    """

    valeur = models.TextField(
        verbose_name="Valeur du paramètre"
    )
    """
    Stocke la valeur du paramètre sous forme de texte.
    - Peut contenir un nombre (ex: "50"), un booléen ("true" / "false") ou une URL.
    - Si le paramètre est complexe (ex: une liste JSON), la valeur peut contenir un JSON stringifié.
    """

    description = models.TextField(
        null=True, 
        blank=True, 
        verbose_name="Description du paramètre"
    )
    """
    Explication optionnelle du rôle du paramètre.
    Permet de documenter les clés stockées et de faciliter leur gestion.
    """

    def __str__(self):
        """Retourne la clé du paramètre pour une meilleure lisibilité en back-office."""
        return self.cle

    class Meta:
        verbose_name = "Paramètre"
        verbose_name_plural = "Paramètres"
        ordering = ['cle']
    """
    - Trie les paramètres par ordre alphabétique de leur clé.
    - Facilite l'affichage dans l'administration et dans les interfaces utilisateur.
    """
