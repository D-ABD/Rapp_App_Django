from django.contrib import admin
from ..models import Centre


@admin.register(Centre)
class CentreAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code_postal', 'created_at', 'updated_at')
    list_filter = ('code_postal',)
    search_fields = ('nom', 'code_postal')
    ordering = ('nom',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Informations', {
            'fields': ('nom', 'code_postal')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )