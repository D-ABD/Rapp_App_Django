from django.contrib import admin
from ..models.recherches import Recherche


@admin.register(Recherche)
class RechercheAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour la gestion des recherches effectuées par les utilisateurs.
    """

    # ✅ Affichage des principales informations dans la liste
    list_display = (
        "terme_recherche", "filtre_centre", "filtre_type_offre", 
        "filtre_statut", "date_debut", "date_fin", 
        "nombre_resultats", "temps_execution", "created_at"
    )

    # ✅ Ajout de filtres pour affiner les recherches dans l'admin
    list_filter = (
        "filtre_centre", "filtre_type_offre", "filtre_statut", 
        "date_debut", "date_fin", "created_at"
    )

    # ✅ Recherche rapide sur certains champs
    search_fields = ("terme_recherche", "filtre_centre__nom", "filtre_type_offre__nom", "filtre_statut__nom")

    # ✅ Champs en lecture seule pour éviter des modifications involontaires
    readonly_fields = ("nombre_resultats", "temps_execution", "created_at", "updated_at")

    # ✅ Organisation des champs dans l'interface d'administration
    fieldsets = (
        ("Détails de la recherche", {
            "fields": ("terme_recherche",)
        }),
        ("Filtres appliqués", {
            "fields": ("filtre_centre", "filtre_type_offre", "filtre_statut", "date_debut", "date_fin")
        }),
        ("Informations sur les résultats", {
            "fields": ("nombre_resultats", "temps_execution"),
            "classes": ("collapse",)  # Permet de masquer cette section par défaut
        }),
        ("Métadonnées", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    # ✅ Configuration de l'affichage dans l'admin
    ordering = ("-created_at",)  # Trie les recherches du plus récent au plus ancien
    list_per_page = 25  # Nombre de recherches affichées par page


    def a_trouve_resultats_display(self, obj):
        """
        Affiche un ✅ si la recherche a trouvé des résultats, sinon ❌.
        """
        return "✅ Oui" if obj.a_trouve_resultats else "❌ Non"
    a_trouve_resultats_display.short_description = "Résultats trouvés"

