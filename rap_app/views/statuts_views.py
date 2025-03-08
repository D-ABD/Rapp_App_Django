from django.urls import reverse_lazy
from django.db.models import Count
from django.contrib.auth.mixins import PermissionRequiredMixin
import random

from ..models import Statut, Formation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView


def generate_random_color():
    """
    Génère une couleur hexadécimale aléatoire si l'utilisateur ne la définit pas.
    Exemple de sortie : "#A3B2C1"
    """
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))


class StatutListView(BaseListView):
    """Liste des statuts de formation"""
    model = Statut
    context_object_name = 'statuts'
    template_name = 'statuts/statut_list.html'  # ✅ Ajout du chemin du template
    
    def get_queryset(self):
        """
        Récupère les statuts de formation avec un comptage des formations associées.
        """
        queryset = super().get_queryset().annotate(
            nb_formations=Count('formations')
        )
        
        # 🔍 Recherche par nom
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(nom__icontains=q)
            
        return queryset.order_by('nom')
    
    def get_context_data(self, **kwargs):
        """
        Ajoute les filtres appliqués au contexte pour les afficher dans le template.
        """
        context = super().get_context_data(**kwargs)
        context['filters'] = {
            'q': self.request.GET.get('q', ''),
        }
        return context
    def get_nom_display(self):
        """
        Retourne le nom du statut. Si le statut est 'Autre', affiche la description à la place.
        """
        if self.nom == self.AUTRE and self.description_autre:
            return self.description_autre
        return dict(self.STATUT_CHOICES).get(self.nom, self.nom)  # Retourne le nom du statut normal


class StatutDetailView(BaseDetailView):
    """Détail d'un statut de formation"""
    model = Statut
    context_object_name = 'statut'
    template_name = 'statuts/statut_detail.html'  # ✅ Ajout du chemin du template
    
    def get_context_data(self, **kwargs):
        """
        Ajoute les formations associées au statut dans le contexte.
        """
        context = super().get_context_data(**kwargs)
        context['formations'] = Formation.objects.filter(
            statut=self.object
        ).select_related('centre', 'type_offre').order_by('-start_date')
        return context


class StatutCreateView(PermissionRequiredMixin, BaseCreateView):
    """Création d'un statut de formation"""
    model = Statut
    permission_required = 'rap_app.add_statut'
    fields = ['nom', 'couleur', 'description_autre']
    success_url = reverse_lazy('statut-list')
    template_name = 'statuts/statut_form.html'  # ✅ Ajout du chemin du template
    
    def form_valid(self, form):
        """
        Vérifie si une couleur est fournie, sinon assigne une couleur aléatoire.
        """
        statut = form.save(commit=False)
        if not statut.couleur:
            statut.couleur = generate_random_color()
        statut.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """
        Ajoute un titre dynamique au contexte du template.
        """
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter un statut de formation"
        return context


class StatutUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Mise à jour d'un statut de formation"""
    model = Statut
    permission_required = 'rap_app.change_statut'
    fields = ['nom', 'couleur', 'description_autre']
    template_name = 'statuts/statut_form.html'  # ✅ Même template que pour la création
    
    def form_valid(self, form):
        """
        Vérifie que la couleur est définie, sinon génère une couleur automatique.
        """
        statut = form.save(commit=False)
        if not statut.couleur:
            statut.couleur = generate_random_color()
        statut.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """
        Ajoute un titre dynamique au contexte.
        """
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier le statut : {self.object.get_nom_display()}"
        return context


class StatutDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """Suppression d'un statut de formation"""
    model = Statut
    permission_required = 'rap_app.delete_statut'
    success_url = reverse_lazy('statut-list')
    template_name = 'statuts/statut_confirm_delete.html'  # ✅ Ajout du chemin du template
