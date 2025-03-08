from django.contrib import admin
from django.utils.html import format_html
from ..models import Statut


@admin.register(Statut)
class StatutAdmin(admin.ModelAdmin):
    list_display = ('get_nom_display', 'couleur_display', 'description_autre', 'created_at')
    list_filter = ('nom',)
    search_fields = ('nom', 'description_autre')
    readonly_fields = ('created_at', 'updated_at', 'couleur_display')
    fieldsets = (
        ('Informations', {
            'fields': ('nom', 'couleur', 'couleur_display', 'description_autre')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_nom_display(self, obj):
        return obj.get_nom_display()
    get_nom_display.short_description = 'Statut'
    get_nom_display.admin_order_field = 'nom'
    
    def couleur_display(self, obj):
        """Affiche un échantillon visuel de la couleur."""
        if obj.couleur:
            return format_html(
                '<div style="display:inline-block; width:100px; height:25px; background-color:{}; '
                'border:1px solid #ddd; border-radius:3px;"></div>', 
                obj.couleur
            )
        return "-"
    couleur_display.short_description = 'Aperçu de la couleur'