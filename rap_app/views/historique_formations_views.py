from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Q
from django.http import JsonResponse, HttpResponse
import csv

from ..models import HistoriqueFormation, Formation
from .base_views import BaseListView, BaseDetailView


class HistoriqueFormationListView(BaseListView):
    """Liste des historiques de formation"""
    model = HistoriqueFormation
    context_object_name = 'historiques'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('formation', 'utilisateur')
        
        # Filtrage par formation
        formation_id = self.request.GET.get('formation')
        if formation_id:
            queryset = queryset.filter(formation_id=formation_id)
        
        # Filtrage par utilisateur
        utilisateur_id = self.request.GET.get('utilisateur')
        if utilisateur_id:
            queryset = queryset.filter(utilisateur_id=utilisateur_id)
        
        # Filtrage par action
        action = self.request.GET.get('action')
        if action:
            queryset = queryset.filter(action__icontains=action)
        
        # Filtrage par date
        date_debut = self.request.GET.get('date_debut')
        if date_debut:
            queryset = queryset.filter(created_at__date__gte=date_debut)
            
        date_fin = self.request.GET.get('date_fin')
        if date_fin:
            queryset = queryset.filter(created_at__date__lte=date_fin)
        
        # Recherche globale
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(action__icontains=q) |
                Q(formation__nom__icontains=q) |
                Q(utilisateur__username__icontains=q) |
                Q(utilisateur__first_name__icontains=q) |
                Q(utilisateur__last_name__icontains=q)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Liste des formations pour le filtre
        context['formations'] = Formation.objects.all().order_by('nom')
        
        # Filtres appliqués
        context['filters'] = {
            'formation': self.request.GET.get('formation', ''),
            'utilisateur': self.request.GET.get('utilisateur', ''),
            'action': self.request.GET.get('action', ''),
            'date_debut': self.request.GET.get('date_debut', ''),
            'date_fin': self.request.GET.get('date_fin', ''),
            'q': self.request.GET.get('q', ''),
        }
        
        return context


class HistoriqueFormationDetailView(BaseDetailView):
    """Détail d'un historique de formation"""
    model = HistoriqueFormation
    context_object_name = 'historique'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer d'autres historiques de la même formation
        if self.object.formation:
            context['autres_historiques'] = self.object.formation.historique_formations.exclude(
                id=self.object.id
            ).order_by('-created_at')[:5]
        
        return context


class HistoriqueFormationExportView(LoginRequiredMixin, TemplateView):
    """Vue pour exporter les historiques de formation"""
    
    def get(self, request, *args, **kwargs):
        # Récupérer les paramètres de filtrage
        formation_id = request.GET.get('formation')
        utilisateur_id = request.GET.get('utilisateur')
        action = request.GET.get('action')
        date_debut = request.GET.get('date_debut')
        date_fin = request.GET.get('date_fin')
        
        # Construire la requête
        queryset = HistoriqueFormation.objects.select_related('formation', 'utilisateur')
        
        if formation_id:
            queryset = queryset.filter(formation_id=formation_id)
        
        if utilisateur_id:
            queryset = queryset.filter(utilisateur_id=utilisateur_id)
        
        if action:
            queryset = queryset.filter(action__icontains=action)
        
        if date_debut:
            queryset = queryset.filter(created_at__date__gte=date_debut)
            
        if date_fin:
            queryset = queryset.filter(created_at__date__lte=date_fin)
        
        # Export en CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="historique_formations.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Formation', 'Utilisateur', 'Action', 
            'Ancien statut', 'Nouveau statut', 
            'Inscrits CRIF', 'Inscrits MP', 'Total inscrits', 'Total places', 
            'Taux remplissage', 'Date'
        ])
        
        for historique in queryset:
            writer.writerow([
                historique.id,
                historique.formation.nom if historique.formation else 'N/A',
                str(historique.utilisateur) if historique.utilisateur else 'N/A',
                historique.action,
                historique.ancien_statut or 'N/A',
                historique.nouveau_statut or 'N/A',
                historique.inscrits_crif or 0,
                historique.inscrits_mp or 0,
                historique.inscrits_total or 0,
                historique.total_places or 0,
                "{:.2f}%".format(historique.taux_remplissage) if historique.taux_remplissage else '0.00%',
                historique.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response