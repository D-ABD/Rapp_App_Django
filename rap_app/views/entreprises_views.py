from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models.entreprises import Entreprise

from ..models import  Formation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView


class EntrepriseListView(BaseListView):
    """Vue listant toutes les entreprises avec des statistiques"""
    model = Entreprise
    context_object_name = 'entreprises'
    template_name = 'entreprises/entreprise_list.html'
    
    def get_queryset(self):
        """
        Récupère la liste des entreprises en annotant des statistiques :
        - Nombre de formations associées à chaque entreprise
        """
        queryset = super().get_queryset().annotate(
            nb_formations=Count('formations')
        )
        
        # Filtrage par nom de l'entreprise
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(nom__icontains=q)
            
        # Filtrage par secteur d'activité
        secteur = self.request.GET.get('secteur')
        if secteur:
            queryset = queryset.filter(secteur_activite__icontains=secteur)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Ajoute des statistiques générales et les filtres appliqués au contexte de la page.
        """
        context = super().get_context_data(**kwargs)
        
        # Statistiques globales
        context['total_entreprises'] = Entreprise.objects.count()
        context['total_formations'] = Formation.objects.count()
        
        # Secteurs d'activité uniques pour le filtre
        secteurs = Entreprise.objects.exclude(secteur_activite__isnull=True).exclude(secteur_activite='').values_list('secteur_activite', flat=True).distinct()
        context['secteurs'] = secteurs
        
        # Filtres actuellement appliqués
        context['filters'] = {
            'q': self.request.GET.get('q', ''),
            'secteur': self.request.GET.get('secteur', ''),
        }
        
        return context


class EntrepriseDetailView(BaseDetailView):
    """Vue affichant les détails d'une entreprise"""
    model = Entreprise
    context_object_name = 'entreprise'
    template_name = 'entreprises/entreprise_detail.html'

    def get_context_data(self, **kwargs):
        """Ajoute au contexte les formations associées à l'entreprise"""
        context = super().get_context_data(**kwargs)
        
        # Récupération des formations associées à l'entreprise
        formations = self.object.formations.select_related('type_offre', 'statut', 'centre').order_by('-start_date')

        # Filtrage des formations par type d'offre
        type_offre = self.request.GET.get('type_offre')
        if type_offre:
            formations = formations.filter(type_offre_id=type_offre)

        # Filtrage des formations par statut
        statut = self.request.GET.get('statut')
        if statut:
            formations = formations.filter(statut_id=statut)

        context['formations'] = formations
        
        return context


class EntrepriseCreateView(PermissionRequiredMixin, BaseCreateView):
    """Vue permettant de créer une nouvelle entreprise"""
    model = Entreprise
    permission_required = 'rap_app.add_entreprise'
    fields = ['nom', 'secteur_activite', 'contact_nom', 'contact_poste', 
              'contact_telephone', 'contact_email', 'description']
    success_url = reverse_lazy('entreprise-list')
    template_name = 'entreprises/entreprise_form.html'
    
    def get_context_data(self, **kwargs):
        """
        Ajoute un titre personnalisé au contexte.
        """
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter une entreprise"
        return context
    
class EntrepriseCreateViewFormation(PermissionRequiredMixin, BaseCreateView):
    """Vue permettant de créer une entreprise et de l'associer à une formation"""
    model = Entreprise
    permission_required = 'rap_app.add_entreprise'
    fields = ['nom', 'secteur_activite', 'contact_nom', 'contact_poste', 
              'contact_telephone', 'contact_email', 'description']
    template_name = 'entreprises/entreprise_formation_form.html'

    def form_valid(self, form):
        """Associe l'entreprise créée à la formation spécifiée dans l'URL"""
        formation_id = self.kwargs.get('formation_id')
        formation = get_object_or_404(Formation, pk=formation_id)
        
        # Sauvegarde de l'entreprise
        self.object = form.save()
        
        # Ajout de l'entreprise à la formation
        formation.entreprises.add(self.object)
        formation.save()
        
        messages.success(self.request, "L'entreprise a été créée et associée à la formation avec succès.")
        return HttpResponseRedirect(reverse_lazy('formation-detail', kwargs={'pk': formation_id}))

    def get_context_data(self, **kwargs):
        """Ajoute un titre dynamique au contexte"""
        context = super().get_context_data(**kwargs)
        formation_id = self.kwargs.get('formation_id')
        formation = get_object_or_404(Formation, pk=formation_id)
        context['titre'] = f"Ajouter une entreprise à la formation : {formation.nom}"
        return context


class EntrepriseUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Vue permettant de modifier une entreprise existante"""
    model = Entreprise
    permission_required = 'rap_app.change_entreprise'
    fields = ['nom', 'secteur_activite', 'contact_nom', 'contact_poste', 
              'contact_telephone', 'contact_email', 'description']
    template_name = 'entreprises/entreprise_form.html'
    
    def get_success_url(self):
        """Redirige vers le détail de l'entreprise après modification"""
        return reverse_lazy('entreprise-detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        """
        Ajoute un titre dynamique au contexte en fonction de l'entreprise modifiée.
        """
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier l'entreprise : {self.object.nom}"
        return context


class EntrepriseDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """Vue permettant de supprimer une entreprise"""
    model = Entreprise
    permission_required = 'rap_app.delete_entreprise'
    success_url = reverse_lazy('entreprise-list')
    template_name = 'entreprises/entreprise_confirm_delete.html'