from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect, get_object_or_404

from ..models import Commentaire, Formation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView


class CommentaireListView(BaseListView):
    """Vue listant tous les commentaires avec options de filtrage"""
    model = Commentaire
    context_object_name = 'commentaires'
    template_name = 'commentaires/commentaire_list.html'
    
    def get_queryset(self):
        """
        Récupère la liste des commentaires avec possibilité de filtrage par:
        - Formation associée
        - Utilisateur
        - Contenu (recherche textuelle)
        """
        queryset = super().get_queryset().select_related('formation', 'utilisateur')
        
        # Filtrage par formation
        formation_id = self.request.GET.get('formation')
        if formation_id:
            queryset = queryset.filter(formation_id=formation_id)
            
        # Filtrage par utilisateur
        utilisateur_id = self.request.GET.get('utilisateur')
        if utilisateur_id:
            queryset = queryset.filter(utilisateur_id=utilisateur_id)
            
        # Recherche textuelle
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(contenu__icontains=q)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        """Ajout des filtres actuels et des options de filtre au contexte"""
        context = super().get_context_data(**kwargs)
        
        # Filtres actuellement appliqués
        context['filters'] = {
            'formation': self.request.GET.get('formation', ''),
            'utilisateur': self.request.GET.get('utilisateur', ''),
            'q': self.request.GET.get('q', ''),
        }
        
        # Liste des formations pour le filtrage
        context['formations'] = Formation.objects.all()
        
        return context


class CommentaireDetailView(BaseDetailView):
    """Vue affichant les détails d'un commentaire"""
    model = Commentaire
    context_object_name = 'commentaire'
    template_name = 'commentaires/commentaire_detail.html'


class CommentaireCreateView(BaseCreateView):
    """Vue permettant de créer un nouveau commentaire"""
    model = Commentaire
    fields = ['formation', 'contenu', 'saturation']
    template_name = 'commentaires/commentaire_form.html'
    
    def get_initial(self):
        """Pré-remplit le formulaire avec la formation si spécifiée dans l'URL"""
        initial = super().get_initial()
        formation_id = self.request.GET.get('formation')
        if formation_id:
            initial['formation'] = formation_id
        return initial
    
    def form_valid(self, form):
        """Associe automatiquement l'utilisateur connecté au commentaire"""
        form.instance.utilisateur = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        """Redirige vers la formation associée après création"""
        return reverse_lazy('formation-detail', kwargs={'pk': self.object.formation.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter un commentaire"
        return context


class CommentaireUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Vue permettant de modifier un commentaire existant"""
    model = Commentaire
    permission_required = 'rap_app.change_commentaire'
    fields = ['contenu', 'saturation']
    template_name = 'commentaires/commentaire_form.html'
    
    def get_success_url(self):
        """Redirige vers la formation associée après modification"""
        return reverse_lazy('formation-detail', kwargs={'pk': self.object.formation.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier le commentaire du {self.object.created_at.strftime('%d/%m/%Y')}"
        return context


class CommentaireDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """Vue permettant de supprimer un commentaire"""
    model = Commentaire
    permission_required = 'rap_app.delete_commentaire'
    template_name = 'commentaires/commentaire_confirm_delete.html'
    
    def get_success_url(self):
        """Redirige vers la formation associée après suppression"""
        formation_id = self.object.formation.id
        return reverse_lazy('formation-detail', kwargs={'pk': formation_id})