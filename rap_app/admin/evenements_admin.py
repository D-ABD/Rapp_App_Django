from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from ..models import Evenement


@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = ('type_evenement_display', 'event_date', 'formation_link', 
                   'details_preview', 'created_at', 'event_date')
    list_filter = ('type_evenement', 'event_date', 'formation__centre')
    search_fields = ('formation__nom', 'details', 'description_autre')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'event_date'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('formation', 'type_evenement', 'description_autre', 'event_date')
        }),
        ('Détails', {
            'fields': ('details',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def formation_link(self, obj):
        if obj.formation and obj.formation.id:
            url = reverse('admin:rap_app_formation_change', args=[obj.formation.id])
            return format_html('<a href="{}">{}</a>', url, obj.formation)
        return "Aucune formation"


    def type_evenement_display(self, obj):
        if obj.type_evenement == Evenement.AUTRE and obj.description_autre:
            return obj.description_autre
        return obj.get_type_evenement_display()
    type_evenement_display.short_description = "Type d'événement"
    type_evenement_display.admin_order_field = 'type_evenement'

    def details_preview(self, obj):
        if obj.details:
            # Tronquer les détails s'ils sont trop longs
            preview = obj.details[:50] + ('...' if len(obj.details) > 50 else '')
            return preview
        return "-"
    details_preview.short_description = 'Détails'