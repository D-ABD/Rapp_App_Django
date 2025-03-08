from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models import Evenement, Formation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView


class EvenementListView(BaseListView):
    """Liste des événements"""
    model = Evenement
    context_object_name = 'evenements'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('formation', 'formation__centre')
        
        # Filtrage par formation
        formation_id = self.request.GET.get('formation')
        if formation_id:
            queryset = queryset.filter(formation_id=formation_id)
        
        # Filtrage par type d'événement
        type_evenement = self.request.GET.get('type')
        if type_evenement:
            queryset = queryset.filter(type_evenement=type_evenement)
        
        # Filtrage par date
        date_debut = self.request.GET.get('date_debut')
        if date_debut:
            queryset = queryset.filter(event_date__gte=date_debut)
        
        date_fin = self.request.GET.get('date_fin')
        if date_fin:
            queryset = queryset.filter(event_date__lte=date_fin)
            
        # Recherche par description
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(details__icontains=q) | queryset.filter(description_autre__icontains=q)
        
        return queryset.order_by('-event_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Liste des formations pour le filtre
        context['formations'] = Formation.objects.formations_actives().order_by('nom')
        
        # Types d'événements pour le filtre
        context['types_evenement'] = Evenement.TYPE_EVENEMENT_CHOICES
        
        # Filtres appliqués
        context['filters'] = {
            'formation': self.request.GET.get('formation', ''),
            'type': self.request.GET.get('type', ''),
            'date_debut': self.request.GET.get('date_debut', ''),
            'date_fin': self.request.GET.get('date_fin', ''),
            'q': self.request.GET.get('q', ''),
        }
        
        return context


class EvenementDetailView(BaseDetailView):
    """Détail d'un événement"""
    model = Evenement
    context_object_name = 'evenement'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer d'autres événements de la même formation
        if self.object.formation:
            context['autres_evenements'] = self.object.formation.evenements.exclude(
                id=self.object.id
            ).order_by('-event_date')[:5]
        
        return context


class EvenementCreateView(PermissionRequiredMixin, BaseCreateView):
    """Création d'un événement"""
    model = Evenement
    permission_required = 'rap_app.add_evenement'
    fields = ['formation', 'type_evenement', 'event_date', 'details', 'description_autre']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter un événement"
        
        # Pré-sélectionner la formation si fournie dans l'URL
        formation_id = self.request.GET.get('formation')
        if formation_id:
            try:
                formation = Formation.objects.get(pk=formation_id)
                context['formation_preselected'] = formation
            except Formation.DoesNotExist:
                pass
        
        return context
    
    def get_success_url(self):
        formation_id = self.object.formation.id if self.object.formation else None
        if formation_id and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': formation_id})
        return reverse('evenement-list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Pré-sélectionner la formation si fournie dans l'URL
        formation_id = self.request.GET.get('formation')
        if formation_id:
            try:
                formation = Formation.objects.get(pk=formation_id)
                form.initial['formation'] = formation
            except Formation.DoesNotExist:
                pass
        
        return form
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Rediriger vers la formation si demandé
        if self.object.formation and self.request.GET.get('redirect_to_formation') == 'true':
            messages.success(self.request, f"Événement ajouté à la formation {self.object.formation.nom}")
        
        return response


class EvenementUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Mise à jour d'un événement"""
    model = Evenement
    permission_required = 'rap_app.change_evenement'
    fields = ['formation', 'type_evenement', 'event_date', 'details', 'description_autre']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier l'événement du {self.object.event_date}"
        return context
    
    def get_success_url(self):
        # Rediriger vers la formation si l'événement est lié à une formation
        if self.object.formation and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': self.object.formation.id})
        return reverse('evenement-detail', kwargs={'pk': self.object.pk})


class EvenementDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """Suppression d'un événement"""
    model = Evenement
    permission_required = 'rap_app.delete_evenement'
    
    def get_success_url(self):
        # Rediriger vers la formation si l'événement est lié à une formation
        formation_id = self.object.formation.id if self.object.formation else None
        if formation_id and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': formation_id})
        return reverse('evenement-list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        formation = self.object.formation
        
        # Appeler la méthode parent pour supprimer l'objet
        response = super().delete(request, *args, **kwargs)
        
        # Message de confirmation avec référence à la formation
        if formation:
            messages.success(request, f"Événement supprimé de la formation {formation.nom}")
        else:
            messages.success(request, "Événement supprimé avec succès")
            
        return response