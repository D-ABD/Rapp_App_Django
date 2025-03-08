from django.db import models
from django.utils.timezone import now  # Utilise Django timezone pour éviter les problèmes UTC

class BaseModel(models.Model):
    """
    Modèle de base pour tous les modèles de l'application.
    Il inclut la gestion automatique de `created_at` et `updated_at`.
    """

    created_at = models.DateTimeField(default=now, editable=False, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    class Meta:
        abstract = True  # Empêche Django de créer une table pour ce modèle
