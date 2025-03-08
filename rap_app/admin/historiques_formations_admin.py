from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.auth import get_user_model
from ..models.historique_formations import HistoriqueFormation


Utilisateur = get_user_model()  # Récupère le modèle utilisateur actif


@admin.register(HistoriqueFormation)
class HistoriqueFormationAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour la gestion de l'historique des formations.
    """

    list_display = (
        "formation_link",
        "action",
        "utilisateur_link",
        "statut_changement",
        "inscrits_progression",
        "taux_remplissage_display",
        "created_at"
    )

    list_filter = (
        "action",
        "formation__centre",
        "formation__type_offre",
        "ancien_statut",
        "nouveau_statut",
        "semaine",
        "mois",
        "annee",
        "created_at"
    )

    search_fields = (
        "formation__nom",
        "utilisateur__username",
        "action",
        "ancien_statut",
        "nouveau_statut"
    )

    readonly_fields = (
        "formation",
        "utilisateur",
        "action",
        "ancien_statut",
        "nouveau_statut",
        "inscrits_total",
        "inscrits_crif",
        "inscrits_mp",
        "total_places",
        "taux_remplissage",
        "semaine",
        "mois",
        "annee",
        "details",
        "created_at",
        "updated_at",
    )

    date_hierarchy = "created_at"

    fieldsets = (
        ("Détails de l'Action", {
            "fields": ("formation", "utilisateur", "action", "ancien_statut", "nouveau_statut")
        }),
        ("Statistiques des Inscriptions", {
            "fields": ("inscrits_total", "inscrits_crif", "inscrits_mp", "total_places", "taux_remplissage")
        }),
        ("Période de Modification", {
            "fields": ("semaine", "mois", "annee")
        }),
        ("Détails Supplémentaires", {
            "fields": ("details",),
            "classes": ("collapse",)
        }),
        ("Métadonnées", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    ordering = ("-created_at",)
    list_per_page = 25

    ### ✅ **🔗 Ajout de liens cliquables**

    def formation_link(self, obj):
        """Ajoute un lien vers la formation associée."""
        if obj.formation:
            url = reverse("admin:rap_app_formation_change", args=[obj.formation.id])
            return format_html('<a href="{}">{}</a>', url, obj.formation.nom)
        return "Formation inconnue"

    formation_link.short_description = "Formation"
    formation_link.admin_order_field = "formation__nom"

    def utilisateur_link(self, obj):
        """Ajoute un lien vers l'utilisateur ayant effectué la modification."""
        if obj.utilisateur:
            url = reverse("admin:rap_app_utilisateur_change", args=[obj.utilisateur.id])
            return format_html('<a href="{}">{}</a>', url, obj.utilisateur.username)
        return "Utilisateur inconnu"

    utilisateur_link.short_description = "Utilisateur"
    utilisateur_link.admin_order_field = "utilisateur__username"

    def statut_changement(self, obj):
        """Affiche l'ancien et le nouveau statut de la formation."""
        if obj.ancien_statut and obj.nouveau_statut:
            return format_html('<span title="Ancien: {0}">{0} → {1}</span>', obj.ancien_statut, obj.nouveau_statut)
        return "-"

    statut_changement.short_description = "Changement de statut"

    def inscrits_progression(self, obj):
        """Affiche la progression des inscriptions."""
        if obj.inscrits_total is not None and obj.total_places:
            return format_html('{}/{} ({:.1f}%)', obj.inscrits_total, obj.total_places, obj.taux_remplissage)
        return "-"

    inscrits_progression.short_description = "Progression des inscriptions"

    def taux_remplissage_display(self, obj):
        """Affiche le taux de remplissage avec un %."""
        if obj.taux_remplissage is not None:
            return f"{obj.taux_remplissage:.1f} %"
        return "-"

    taux_remplissage_display.short_description = "Taux de remplissage"

    def has_add_permission(self, request):
        """Empêche l'ajout manuel d'un historique."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Empêche la suppression manuelle des historiques."""
        return False
