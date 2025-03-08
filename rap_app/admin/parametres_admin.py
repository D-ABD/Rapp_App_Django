from django.contrib import admin
from ..models import Parametre


@admin.register(Parametre)
class ParametreAdmin(admin.ModelAdmin):
    list_display = ('cle', 'valeur_preview', 'description_preview', 'updated_at')
    search_fields = ('cle', 'valeur', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Paramètre', {
            'fields': ('cle', 'valeur', 'description')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def valeur_preview(self, obj):
        # Tronquer la valeur si elle est trop longue
        preview = obj.valeur[:50] + ('...' if len(obj.valeur) > 50 else '')
        return preview
    valeur_preview.short_description = 'Valeur'

    def description_preview(self, obj):
        if obj.description:
            # Tronquer la description si elle est trop longue
            preview = obj.description[:50] + ('...' if len(obj.description) > 50 else '')
            return preview
        return "-"
    description_preview.short_description = 'Description'