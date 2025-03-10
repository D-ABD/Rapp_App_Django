from django.contrib import admin
from django.utils.html import format_html
from django.db.models import F, Sum

from ..models.formations import Formation

@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    """
    Administration du modèle Formation avec fonctionnalités avancées
    """
    # Champs affichés dans la liste des formations
    list_display = (
        'nom', 
        'centre', 
        'type_offre', 
        'statut', 
        'start_date', 
        'end_date', 
        'places_dispo_display', 
        'taux_saturation_display'
    )
    
    # Filtres dans la barre latérale
    list_filter = (
        'centre', 
        'statut', 
        'type_offre', 
        'start_date', 
        'end_date', 
        'convocation_envoie'
    )
    
    # Champs de recherche
    search_fields = (
        'nom', 
        'num_kairos', 
        'num_offre', 
        'num_produit', 
        'assistante'
    )
    
    # Actions personnalisées
    actions = [
        'marquer_convocation_envoyee', 
        'reset_convocation_envoyee'
    ]
    
    # Champs pour édition rapide depuis la liste
    list_editable = (
        'statut',
    )
    
    # Champs cliquables dans la liste
    list_display_links = (
        'nom',
    )
    
    # Pagination pour la liste des formations
    list_per_page = 20
    
    # Filtres date dans le panneau latéral
    date_hierarchy = 'start_date'
    
    # Groupes de champs dans le formulaire d'édition
    fieldsets = (
        ('Informations générales', {
            'fields': (
                'nom', 
                'centre', 
                'type_offre', 
                'statut',
                'utilisateur'
            )
        }),
        ('Dates et identifiants', {
            'fields': (
                'start_date', 
                'end_date', 
                'num_kairos', 
                'num_offre', 
                'num_produit'
            )
        }),
        ('Gestion des places', {
            'fields': (
                ('prevus_crif', 'inscrits_crif'),
                ('prevus_mp', 'inscrits_mp'),
                'cap',
                'entresformation'
            )
        }),
        ('Recrutement', {
            'fields': (
                'nombre_candidats', 
                'nombre_entretiens', 
                'convocation_envoie'
            )
        }),
        ('Informations supplémentaires', {
            'fields': (
                'assistante', 
                'nombre_evenements',
                'dernier_commentaire',
                'entreprises'
            ),
            'classes': ('collapse',)  # Cette section est rétractable
        })
    )
    
    # Sauvegarde automatique des ManyToMany relations
    save_on_top = True
    
    # Relations many-to-many dans un widget filtrable
    filter_horizontal = ('entreprises',)
    
    # Méthodes pour les champs personnalisés dans l'affichage en liste
    
    def places_dispo_display(self, obj):
        """Affiche le nombre de places disponibles avec formatage"""
        places = obj.get_places_disponibles()
        color = 'green' if places > 5 else 'orange' if places > 0 else 'red'
        return format_html('<span style="color: {};">{}</span>', color, places)
    places_dispo_display.short_description = "Places disponibles"
    places_dispo_display.admin_order_field = 'places_disponibles'
    
    def taux_saturation_display(self, obj):
        """Affiche le taux de saturation avec une barre de progression"""
        taux = obj.get_taux_saturation()
        color = 'green' if taux < 70 else 'orange' if taux < 95 else 'red'
        return format_html(
            '<div style="width:100px; border:1px solid #ccc;">'
            '<div style="width:{}px; height:10px; background-color:{};">&nbsp;</div>'
            '</div> {}%',
            min(int(taux), 100), color, round(taux, 1)
        )
    taux_saturation_display.short_description = "Taux de saturation"
    taux_saturation_display.admin_order_field = 'taux_saturation'
    
    # Actions personnalisées
    
    def marquer_convocation_envoyee(self, request, queryset):
        """Marque les convocations comme envoyées pour les formations sélectionnées"""
        updated = queryset.update(convocation_envoie=True)
        self.message_user(request, f"{updated} formations marquées avec convocations envoyées.")
    marquer_convocation_envoyee.short_description = "Marquer les convocations comme envoyées"
    
    def reset_convocation_envoyee(self, request, queryset):
        """Réinitialise le statut d'envoi des convocations"""
        updated = queryset.update(convocation_envoie=False)
        self.message_user(request, f"Statut d'envoi des convocations réinitialisé pour {updated} formations.")
    reset_convocation_envoyee.short_description = "Réinitialiser statut d'envoi des convocations"
    
    # Surcharge pour ajouter des annotations
    def get_queryset(self, request):
        """Surcharge pour ajouter des calculs agrégés à la requête"""
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            places_disponibles=F('prevus_crif') + F('prevus_mp') - F('inscrits_crif') - F('inscrits_mp'),
            taux_saturation=100 * (F('inscrits_crif') + F('inscrits_mp')) / 
                           (F('prevus_crif') + F('prevus_mp'))
        )
        return queryset

    # Statistiques personnalisées
    def changelist_view(self, request, extra_context=None):
        """Ajout de statistiques en haut de la liste des formations"""
        response = super().changelist_view(request, extra_context)
        
        # Uniquement si nous ne faisons pas face à une erreur 404
        if hasattr(response, 'context_data'):
            queryset = self.get_queryset(request)
            
            # Calculer les statistiques globales
            stats = queryset.aggregate(
                total_formations=Sum('id', distinct=True),
                total_places=Sum(F('prevus_crif') + F('prevus_mp')),
                total_inscrits=Sum(F('inscrits_crif') + F('inscrits_mp')),
            )
            
            # Ajouter les statistiques au contexte
            if not extra_context:
                extra_context = {}
            
            # Vérifier que les valeurs ne sont pas None avant de calculer
            if stats['total_places'] and stats['total_inscrits']:
                taux_remplissage = (stats['total_inscrits'] / stats['total_places']) * 100
                extra_context['taux_remplissage_global'] = round(taux_remplissage, 1)
            else:
                extra_context['taux_remplissage_global'] = 0
                
            extra_context.update(stats)
            response.context_data.update(extra_context)
            
        return response
    
    # Esthétique et optimisation des chargements
    
    class Media:
        """Ressources CSS et JS pour l'interface d'admin"""
        css = {
            'all': ('css/admin/formation_admin.css',)
        }
        js = ('js/admin/formation_admin.js',)