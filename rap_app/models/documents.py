from django.db import models
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
import os
from django.conf import settings
from django.core.exceptions import ValidationError
from .base import BaseModel
from .formations import Formation, User


class Document(BaseModel):
    """
    Modèle représentant un document associé à une formation.
    Permet de stocker et gérer différents types de documents (PDF, images, contrats...).
    """

    # Types de documents possibles
    PDF = 'pdf'
    IMAGE = 'image'
    CONTRAT = 'contrat'
    AUTRE = 'autre'

    TYPE_DOCUMENT_CHOICES = [
        (PDF, 'PDF'),
        (IMAGE, 'Image'),
        (CONTRAT, 'Contrat signé'),
        (AUTRE, 'Autre'),
    ]

    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name="documents",  verbose_name="Formation associée")
    nom_fichier = models.CharField(max_length=255, verbose_name="Nom du fichier",db_index=True)
    fichier = models.FileField(upload_to='formations/documents/', verbose_name="Fichier")
    source = models.TextField(null=True, blank=True, verbose_name="Source du document")
    type_document = models.CharField( max_length=20, choices=TYPE_DOCUMENT_CHOICES, default=AUTRE,verbose_name="Type de document")
    taille_fichier = models.PositiveIntegerField(null=True,blank=True, verbose_name="Taille du fichier (Ko)")
    utilisateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        """
        Retourne une représentation lisible du document avec un nom tronqué si nécessaire.
        Exemple : "Guide utilisateur.pdf"
        """
        nom_tronque = self.nom_fichier[:50] + ('...' if len(self.nom_fichier) > 50 else '')
        return f"{nom_tronque} ({self.get_type_document_display()})"
    
    def clean(self):
        """Validation personnalisée pour vérifier la correspondance entre type et extension."""
        super().clean()
        if self.fichier and self.type_document:
            validate_file_extension(self.fichier, self.type_document)

    def save(self, *args, **kwargs):
        """
        - Vérifie les règles de validation avant la sauvegarde (`full_clean()`).
        - Met à jour automatiquement la taille du fichier en Ko.
        """
        self.full_clean()  # Exécute la validation avant la sauvegarde.

        if self.fichier and hasattr(self.fichier, 'size'):
            self.taille_fichier = max(1, self.fichier.size // 1024)  # Au moins 1 Ko pour éviter les zeros
        
        super().save(*args, **kwargs)
    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['nom_fichier']),  # Index pour la recherche rapide
        ]


### 🚀 Validation : Empêcher l'upload d'un fichier invalide
def validate_file_extension(value, type_doc=None):
    """
    Vérifie que le fichier téléchargé correspond bien au type déclaré.
    Le paramètre type_doc peut être passé à la validation.
    """
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = {
        'pdf': ['.pdf'],
        'image': ['.jpg', '.jpeg', '.png', '.gif'],
        'contrat': ['.pdf', '.doc', '.docx'],
        'autre': []  # Autorise tout pour "Autre"
    }
    
    # Si aucun type n'est fourni ou si c'est "autre", on accepte le fichier
    if not type_doc or type_doc == Document.AUTRE:
        return
        
    # Vérifie si l'extension correspond au type fourni
    if ext not in valid_extensions.get(type_doc, []):
        raise ValidationError(f"Le fichier {value.name} ne correspond pas au type {dict(Document.TYPE_DOCUMENT_CHOICES).get(type_doc, type_doc)}.")

### 🚀 Suppression automatique des anciens fichiers avant mise à jour
@receiver(pre_save, sender=Document)
def supprimer_fichier_ancien(sender, instance, **kwargs):
    """
    Supprime l'ancien fichier si un nouveau fichier est uploadé pour éviter l'accumulation de fichiers inutiles.
    """
    if instance.pk:
        ancien_document = Document.objects.get(pk=instance.pk)
        if ancien_document.fichier and ancien_document.fichier != instance.fichier:
            ancien_fichier_path = os.path.join(settings.MEDIA_ROOT, ancien_document.fichier.name)
            if os.path.exists(ancien_fichier_path):
                os.remove(ancien_fichier_path)


### 🚀 Suppression automatique du fichier après suppression d'un Document
@receiver(post_delete, sender=Document)
def supprimer_fichier_apres_suppression(sender, instance, **kwargs):
    """
    Supprime le fichier du stockage lorsque l'objet `Document` est supprimé.
    Évite les erreurs si le fichier a déjà été supprimé.
    """
    if instance.fichier:
        fichier_path = os.path.join(settings.MEDIA_ROOT, instance.fichier.name)
        try:
            if os.path.exists(fichier_path):
                os.remove(fichier_path)
        except Exception as e:
            print(f"Erreur lors de la suppression du fichier {fichier_path}: {e}")
