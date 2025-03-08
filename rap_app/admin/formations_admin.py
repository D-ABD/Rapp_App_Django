from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from ..models.formations import Formation
from ..models.evenements import Evenement
from ..models.documents import Document
from ..models.commentaires import Commentaire


# 🎯 Inline pour ajouter/modifier des événements liés à une formation
class EvenementInline(admin.TabularInline):
    model = Evenement
    extra = 1  # Permet d'ajouter un nouvel événement directement
    fields = ("type_evenement", "event_date", "description_autre")
    readonly_fields = ("event_date",)
    ordering = ["-event_date"]


# 📄 Inline pour ajouter des documents liés à une formation
class DocumentInline(admin.TabularInline):
    model = Document
    extra = 1
    fields = ("nom_fichier", "fichier", "type_document", "source")
    ordering = ["-created_at"]


# 🗨️ Inline pour ajouter des commentaires liés à une formation
class CommentaireInline(admin.TabularInline):
    model = Commentaire
    extra = 1
    fields = ("contenu", "created_at")
    readonly_fields = ("created_at",)
    ordering = ["-created_at"]


@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour la gestion des formations.
    """

    inlines = [EvenementInline, DocumentInline, CommentaireInline]  # Ajoute les inlines !

    list_display = (
        "nom", "centre", "type_offre", "statut", "start_date", "end_date",
        "get_total_places", "get_total_inscrits", "get_a_recruter", "get_saturation",
        "total_evenements", "dernier_commentaire", "is_a_recruter", "utilisateur"
    )

    list_filter = ("centre", "type_offre", "statut", "start_date", "end_date", "convocation_envoie")
    search_fields = ("nom", "num_kairos", "num_offre", "num_produit", "assistante", "dernier_commentaire")

    readonly_fields = (
        "get_total_places", "get_total_inscrits", "get_a_recruter",
        "get_saturation", "dernier_commentaire", "get_documents_list"
    )

    fieldsets = (
        ("Informations générales", {
            "fields": ("nom", "centre", "type_offre", "statut")
        }),
        ("Dates et Identifiants", {
            "fields": ("start_date", "end_date", "num_kairos", "num_offre", "num_produit")
        }),
        ("Gestion des places", {
            "fields": ("prevus_crif", "prevus_mp", "inscrits_crif", "inscrits_mp", "cap")
        }),
        ("Statistiques", {
            "fields": ("nombre_candidats", "nombre_entretiens", "nombre_evenements", "entresformation")
        }),
        ("Suivi du remplissage", {
            "fields": ("get_total_places", "get_total_inscrits", "get_a_recruter", "get_saturation"),
            "classes": ("collapse",)
        }),
        ("Dernier commentaire et entreprise associée", {
            "fields": ("dernier_commentaire", "entreprises"),
        }),
        ("Autres informations", {
            "fields": ("assistante", "convocation_envoie"),
            "classes": ("collapse",)
        }),
        ("Documents associés", {
            "fields": ("get_documents_list",),
            "classes": ("collapse",)
        }),
    )

    def get_total_places(self, obj):
        return obj.total_places
    get_total_places.short_description = "Total Places"

    def get_total_inscrits(self, obj):
        return obj.total_inscrits
    get_total_inscrits.short_description = "Total Inscrits"

    def get_a_recruter(self, obj):
        return obj.a_recruter
    get_a_recruter.short_description = "Places à Recruter"

    def get_saturation(self, obj):
        return f"{obj.saturation:.2f} %" if obj.saturation else "N/A"
    get_saturation.short_description = "Saturation (%)"

    def get_documents_list(self, obj):
        """Génère une liste cliquable des documents associés à la formation."""
        documents = obj.get_documents()
        if not documents:
            return "Aucun document"

        liens = [
            format_html('<a href="{}" target="_blank">{}</a>', doc.fichier.url if doc.fichier else "#", doc.nom_fichier)
            for doc in documents
        ]
        return format_html("<br>".join(liens))


    get_documents_list.short_description = "Documents associés"

    def save_model(self, request, obj, form, change):
        """Met à jour les champs calculés et assigne automatiquement l'utilisateur avant de sauvegarder."""
        
        # Assigne l'utilisateur s'il n'est pas défini
        if not obj.utilisateur:
            obj.utilisateur = request.user
        
        # Mise à jour automatique des valeurs calculées
        obj.saturation = (obj.total_inscrits / obj.total_places) * 100 if obj.total_places > 0 else 0

        # Mise à jour du dernier commentaire
        dernier_commentaire = obj.commentaires.order_by('-created_at').first()
        obj.dernier_commentaire = dernier_commentaire.contenu if dernier_commentaire else None

        super().save_model(request, obj, form, change)

