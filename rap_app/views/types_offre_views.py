from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.contrib.auth.mixins import PermissionRequiredMixin

from ..models import TypeOffre, Formation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView


class TypeOffreListView(BaseListView):
    """Liste des types d'offres de formation"""
    model = TypeOffre
    context_object_name = 'types_offre'
    template_name = "types_offres/typeoffre_list.html"
    
    def get_queryset(self):
        queryset = super().get_queryset().annotate(
            nb_formations=Count('formations')
        )
        
        # Recherche par nom
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(Q(nom__icontains=q) | Q(autre__icontains=q))
        
        return queryset.order_by('nom')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filtres appliqués
        context['filters'] = {
            'q': self.request.GET.get('q', ''),
        }
        
        return context


class TypeOffreDetailView(BaseDetailView):
    """Détail d'un type d'offre de formation"""
    model = TypeOffre
    context_object_name = 'type_offre'
    template_name = "types_offres/typeoffre_detail.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer les formations associées
        context['formations'] = Formation.objects.filter(
            type_offre=self.object
        ).select_related('centre', 'statut').order_by('-start_date')
        
        return context


class TypeOffreCreateView(PermissionRequiredMixin, BaseCreateView):
    """Création d'un type d'offre de formation"""
    model = TypeOffre
    permission_required = 'rap_app.add_typeoffre'
    fields = ['nom', 'autre']
    success_url = reverse_lazy('type-offre-list')
    template_name = "types_offres/typeoffre_form.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter un type d'offre de formation"
        return context


class TypeOffreUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Mise à jour d'un type d'offre de formation"""
    model = TypeOffre
    permission_required = 'rap_app.change_typeoffre'
    fields = ['nom', 'autre']
    template_name = "types_offres/typeoffre_form.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier le type d'offre : {self.object.__str__()}"
        return context


class TypeOffreDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """Suppression d'un type d'offre de formation"""
    model = TypeOffre
    permission_required = 'rap_app.delete_typeoffre'
    success_url = reverse_lazy('type-offre-list')
    template_name = "types_offres/typeoffre_confirm_delete.html"