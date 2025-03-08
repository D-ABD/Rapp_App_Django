from django.contrib import admin
from ..models import Statut


@admin.register(Statut)
class StatutAdmin(admin.ModelAdmin):
    list_display = ('get_nom_display', 'couleur', 'description_autre', 'created_at')
    list_filter = ('nom',)
    search_fields = ('nom', 'description_autre')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Informations', {
            'fields': ('nom', 'couleur', 'description_autre')
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