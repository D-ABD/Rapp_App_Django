from django.contrib import admin
from ..models import TypeOffre


@admin.register(TypeOffre)
class TypeOffreAdmin(admin.ModelAdmin):
    list_display = ('get_nom_display', 'autre', 'created_at')
    list_filter = ('nom',)
    search_fields = ('nom', 'autre')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Informations', {
            'fields': ('nom', 'autre')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_nom_display(self, obj):
        return obj.get_nom_display()
    get_nom_display.short_description = "Type d'offre"
    get_nom_display.admin_order_field = 'nom'