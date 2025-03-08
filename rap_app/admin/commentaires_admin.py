from django.contrib import admin
from django.contrib.auth import get_user_model
from ..models.commentaires import Commentaire



Utilisateur = get_user_model()

@admin.register(Commentaire)
class CommentaireAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour la gestion des commentaires liés aux formations.
    """

    # Affichage des principales informations
    list_display = ("formation", "utilisateur", "contenu", "saturation", "created_at")

    # Ajout de filtres pour faciliter la recherche
    list_filter = ("formation", "utilisateur", "saturation", "created_at")

    # Recherche rapide sur certains champs
    search_fields = ("formation__nom", "utilisateur__username", "contenu")

    # Rendre certains champs en lecture seule
    readonly_fields = ("utilisateur", "created_at")

    # Organisation des champs
    fieldsets = (
        ("Informations générales", {
            "fields": ("formation", "utilisateur")
        }),
        ("Contenu du commentaire", {
            "fields": ("contenu",)
        }),
        ("Données complémentaires", {
            "fields": ("saturation",),
        }),
        ("Métadonnées", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )

    ordering = ("-created_at",)
    list_per_page = 20

def save_model(self, request, obj, form, change):
    """
    Assigne l'utilisateur connecté à l'ajout d'un commentaire.
    """
    if not obj.utilisateur:
        # Vérifie que request.user est bien du bon type
        if isinstance(request.user, Utilisateur):
            obj.utilisateur = request.user
        else:
            obj.utilisateur = Utilisateur.objects.get(pk=request.user.pk)  # Convertit en `Utilisateur`
    
    obj.save()

