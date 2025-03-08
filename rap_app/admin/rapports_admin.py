from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from ..models import Rapport


@admin.register(Rapport)
class RapportAdmin(admin.ModelAdmin):
    list_display = ('periode_dates', 'formation_link', 'inscrits_progression', 
                   'transformation_display', 'nombre_evenements', 'created_at')
    list_filter = ('periode', 'date_debut', 'date_fin', 'formation__centre', 'formation__type_offre')
    search_fields = ('formation__nom',)
    readonly_fields = ('taux_remplissage', 'taux_transformation', 'created_at', 'updated_at')
    date_hierarchy = 'date_fin'
    fieldsets = (
        ('Période', {
            'fields': ('formation', 'periode', 'date_debut', 'date_fin')
        }),
        ('Inscriptions', {
            'fields': ('total_inscrits', 'inscrits_crif', 'inscrits_mp', 'total_places')
        }),
        ('Recrutement', {
            'fields': ('nombre_evenements', 'nombre_candidats', 'nombre_entretiens')
        }),
        ('Statistiques calculées', {
            'fields': ('taux_remplissage', 'taux_transformation'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def formation_link(self, obj):
        if obj.formation:
            url = reverse('admin:rap_app_formation_change', args=[obj.formation.id])
            return format_html('<a href="{}">{}</a>', url, obj.formation)
        return "Rapport global"
    formation_link.short_description = 'Formation'
    formation_link.admin_order_field = 'formation__nom'

    def periode_dates(self, obj):
        return format_html('{} ({} à {})', 
                         obj.get_periode_display(), 
                         obj.date_debut.strftime('%d/%m/%Y'), 
                         obj.date_fin.strftime('%d/%m/%Y'))
    periode_dates.short_description = 'Période'
    periode_dates.admin_order_field = 'date_fin'

    def inscrits_progression(self, obj):
        taux = obj.taux_remplissage
        color = '#4CAF50' if taux >= 80 else '#FFC107' if taux >= 50 else '#F44336'
        return format_html('<span style="color: {};">{}/{} ({})</span>', 
                         color, obj.total_inscrits, obj.total_places, "{:.1f}%".format(taux))
    inscrits_progression.short_description = 'Progression des inscriptions'

    def transformation_display(self, obj):
        taux = obj.taux_transformation
        if obj.nombre_candidats > 0:
            color = '#4CAF50' if taux >= 30 else '#FFC107' if taux >= 15 else '#F44336'
            return format_html('<span style="color: {};">{}</span>', color, "{:.1f}%".format(taux))
        return '-'
    transformation_display.short_description = 'Taux de transformation'