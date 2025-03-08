from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models import Commentaire, Formation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView


class CommentaireListView(BaseListView):
    """Liste des commentaires"""
    model = Commentaire
    context_object_name = 'commentaires'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('formation', 'utilisateur')
        
        # Filtrer par formation si spécifié
        formation_id = self.request.GET.get('formation')
        if formation_id:
            queryset = queryset.filter(formation_id=formation_id)
        
        # Filtrer par utilisateur si spécifié
        utilisateur_id = self.request.GET.get('utilisateur')
        if utilisateur_id:
            queryset = queryset.filter(utilisateur_id=utilisateur_id)
        
        # Recherche dans le contenu
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(contenu__icontains=q)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Formations pour le filtre
        context['formations'] = Formation.objects.formations_actives().order_by('nom')
        
        # Filtres appliqués
        context['filters'] = {
            'formation': self.request.GET.get('formation', ''),
            'utilisateur': self.request.GET.get('utilisateur', ''),
            'q': self.request.GET.get('q', ''),
        }
        
        return context


class CommentaireCreateView(PermissionRequiredMixin, BaseCreateView):
    """Création d'un commentaire"""
    model = Commentaire
    permission_required = 'rap_app.add_commentaire'
    fields = ['formation', 'auteur', 'contenu']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter un commentaire"
        
        # Pré-sélectionner la formation si fournie dans l'URL
        formation_id = self.request.GET.get('formation')
        if formation_id:
            try:
                formation = Formation.objects.get(pk=formation_id)
                context['formation_preselected'] = formation
            except Formation.DoesNotExist:
                pass
        
        return context
    
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
        # Associer l'utilisateur courant au commentaire
        form.instance.utilisateur = self.request.user
        
        # Si le champ auteur est vide, utiliser le nom de l'utilisateur courant
        if not form.instance.auteur:
            form.instance.auteur = self.request.user.get_full_name() or self.request.user.username
        
        return super().form_valid(form)
    
    def get_success_url(self):
        # Si redirigé depuis la vue détaillée d'une formation, y retourner
        if self.object.formation and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': self.object.formation.id})
        return reverse('commentaire-list')


class CommentaireUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Mise à jour d'un commentaire"""
    model = Commentaire
    permission_required = 'rap_app.change_commentaire'
    fields = ['formation', 'auteur', 'contenu']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier le commentaire"
        return context
    
    def get_success_url(self):
        # Si redirigé depuis la vue détaillée d'une formation, y retourner
        if self.object.formation and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': self.object.formation.id})
        return reverse('commentaire-detail', kwargs={'pk': self.object.pk})


class CommentaireDetailView(BaseDetailView):
    """Détail d'un commentaire"""
    model = Commentaire
    context_object_name = 'commentaire'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer d'autres commentaires de la même formation
        if self.object.formation:
            context['autres_commentaires'] = self.object.formation.commentaires.exclude(
                id=self.object.id
            ).order_by('-created_at')[:5]
        
        return context


class CommentaireDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """Suppression d'un commentaire"""
    model = Commentaire
    permission_required = 'rap_app.delete_commentaire'
    
    def get_success_url(self):
        # Rediriger vers la formation si le commentaire est lié à une formation
        formation_id = self.object.formation.id if self.object.formation else None
        if formation_id and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': formation_id})
        return reverse('commentaire-list')