from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone

from ..models import Evenement, Formation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView


class EvenementListView(BaseListView):
    """Vue listant tous les événements avec options de filtrage"""
    model = Evenement
    context_object_name = 'evenements'
    template_name = 'evenements/evenement_list.html'
    
    def get_queryset(self):
        """
        Récupère la liste des événements avec possibilité de filtrage par:
        - Formation associée
        - Type d'événement
        - Date (à venir, passés)
        """
        queryset = super().get_queryset().select_related('formation', 'formation__centre')
        
        # Filtrage par formation
        formation_id = self.request.GET.get('formation')
        if formation_id:
            queryset = queryset.filter(formation_id=formation_id)
            
        # Filtrage par type d'événement
        type_evt = self.request.GET.get('type')
        if type_evt:
            queryset = queryset.filter(type_evenement=type_evt)
            
        # Filtrage par période (à venir/passés)
        periode = self.request.GET.get('periode')
        if periode == 'future':
            queryset = queryset.filter(event_date__gte=timezone.now().date())
        elif periode == 'past':
            queryset = queryset.filter(event_date__lt=timezone.now().date())
            
        # Recherche textuelle
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(details__icontains=q) | 
                Q(description_autre__icontains=q) |
                Q(formation__nom__icontains=q)
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        """Ajout des filtres actuels et des options de filtre au contexte"""
        context = super().get_context_data(**kwargs)
        
        # Filtres actuellement appliqués
        context['filters'] = {
            'formation': self.request.GET.get('formation', ''),
            'type': self.request.GET.get('type', ''),
            'periode': self.request.GET.get('periode', ''),
            'q': self.request.GET.get('q', ''),
        }
        
        # Liste des formations pour le filtrage
        context['formations'] = Formation.objects.all()
        
        # Types d'événements pour le filtrage
        context['types_evenement'] = Evenement.TYPE_EVENEMENT_CHOICES
        
        # Date actuelle pour affichage
        context['now'] = timezone.now().date()
        
        return context


class EvenementDetailView(BaseDetailView):
    """Vue affichant les détails d'un événement"""
    model = Evenement
    context_object_name = 'evenement'
    template_name = 'evenements/evenement_detail.html'


class EvenementCreateView(PermissionRequiredMixin, BaseCreateView):
    """Vue permettant de créer un nouvel événement"""
    model = Evenement
    permission_required = 'rap_app.add_evenement'
    fields = ['formation', 'type_evenement', 'details', 'event_date', 'description_autre']
    template_name = 'evenements/evenement_form.html'
    
    def get_initial(self):
        """Pré-remplit le formulaire avec la formation si spécifiée dans l'URL"""
        initial = super().get_initial()
        formation_id = self.request.GET.get('formation')
        if formation_id:
            initial['formation'] = formation_id
        return initial
    
    def get_success_url(self):
        """Redirige vers la formation associée après création"""
        if self.object.formation:
            return reverse_lazy('formation-detail', kwargs={'pk': self.object.formation.pk})
        return reverse_lazy('evenement-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter un événement"
        # Ajout de la liste des types d'événements
        context['types_evenement'] = Evenement.TYPE_EVENEMENT_CHOICES
        return context


class EvenementUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Vue permettant de modifier un événement existant"""
    model = Evenement
    permission_required = 'rap_app.change_evenement'
    fields = ['formation', 'type_evenement', 'details', 'event_date', 'description_autre']
    template_name = 'evenements/evenement_form.html'
    
    def get_success_url(self):
        """Redirige vers la formation associée après modification"""
        if self.object.formation:
            return reverse_lazy('formation-detail', kwargs={'pk': self.object.formation.pk})
        return reverse_lazy('evenement-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier l'événement du {self.object.event_date.strftime('%d/%m/%Y') if self.object.event_date else ''}"
        # Ajout de la liste des types d'événements
        context['types_evenement'] = Evenement.TYPE_EVENEMENT_CHOICES
        return context


class EvenementDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """Vue permettant de supprimer un événement"""
    model = Evenement
    permission_required = 'rap_app.delete_evenement'
    template_name = 'evenements/evenement_confirm_delete.html'
    
    def get_success_url(self):
        """Redirige vers la formation associée après suppression"""
        if hasattr(self, 'formation_id') and self.formation_id:
            return reverse_lazy('formation-detail', kwargs={'pk': self.formation_id})
        return reverse_lazy('evenement-list')
    
    def delete(self, request, *args, **kwargs):
        """Stocke l'ID de la formation avant suppression pour la redirection"""
        self.object = self.get_object()
        self.formation_id = self.object.formation.id if self.object.formation else None
        return super().delete(request, *args, **kwargs)