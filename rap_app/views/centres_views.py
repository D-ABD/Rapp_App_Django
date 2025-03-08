from django.urls import reverse_lazy
from django.db.models import Count, Sum, F, Q
from django.utils import timezone
from django.contrib.auth.mixins import PermissionRequiredMixin

from ..models import Centre, Formation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView


class CentreListView(BaseListView):
    """Vue listant tous les centres de formation avec des statistiques"""
    model = Centre
    context_object_name = 'centres'
    template_name = 'centres/centre_list.html'  # ✅ Défini explicitement le template
    
    def get_queryset(self):
        """
        Récupère la liste des centres de formation en annotant des statistiques :
        - Nombre total de formations liées à chaque centre.
        - Nombre de formations actives (date de fin >= aujourd'hui OU sans date de fin).
        - Nombre total d'inscrits (CRIF + MP).
        """
        queryset = super().get_queryset().annotate(
            nb_formations=Count('formations'),
            nb_formations_actives=Count(
                'formations',
                filter=Q(formations__end_date__gte=timezone.now()) | Q(formations__end_date__isnull=True)
            ),
            nb_inscrits=Sum(
                F('formations__inscrits_crif') + F('formations__inscrits_mp'),
                default=0
            )
        )
        
        # 🔍 Filtrage par nom du centre
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(nom__icontains=q)
            
        # 🔍 Filtrage par code postal
        cp = self.request.GET.get('code_postal')
        if cp:
            queryset = queryset.filter(code_postal__startswith=cp)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Ajoute des statistiques générales et les filtres appliqués au contexte de la page.
        """
        context = super().get_context_data(**kwargs)
        
        # 📊 Statistiques globales
        context['total_centres'] = Centre.objects.count()
        context['total_formations'] = Formation.objects.count()
        
        # 🔍 Filtres actuellement appliqués
        context['filters'] = {
            'q': self.request.GET.get('q', ''),
            'code_postal': self.request.GET.get('code_postal', ''),
        }
        
        return context


class CentreDetailView(BaseDetailView):
    """Vue affichant les détails d'un centre de formation"""
    model = Centre
    context_object_name = 'centre'
    template_name = 'centres/centre_detail.html'  # Vérifie que ce fichier existe

    def get_context_data(self, **kwargs):
        """Ajoute au contexte les formations associées au centre"""
        context = super().get_context_data(**kwargs)
        
        # 📌 Récupération des formations associées au centre
        formations = self.object.formations.select_related('type_offre', 'statut').order_by('-start_date')

        # 🔍 Filtrage des formations par type d'offre
        type_offre = self.request.GET.get('type_offre')
        if type_offre:
            formations = formations.filter(type_offre_id=type_offre)

        # 🔍 Filtrage des formations par statut
        statut = self.request.GET.get('statut')
        if statut:
            formations = formations.filter(statut_id=statut)

        # 📊 Extraire les choix pour le template
        type_offres = formations.values_list('type_offre__id', 'type_offre__nom').distinct()
        statuts = formations.values_list('statut__id', 'statut__nom').distinct()

        # 📊 Ajouter au contexte
        context.update({
            'formations': formations,
            'type_offres': type_offres,
            'statuts': statuts
        })

        return context



class CentreCreateView(PermissionRequiredMixin, BaseCreateView):
    """Vue permettant de créer un nouveau centre de formation"""
    model = Centre
    permission_required = 'rap_app.add_centre'
    fields = ['nom', 'code_postal']
    success_url = reverse_lazy('centre-list')
    template_name = 'centres/centre_form.html'  # ✅ Vérification du chemin correct

    
    def get_context_data(self, **kwargs):
        """
        Ajoute un titre personnalisé au contexte.
        """
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter un centre de formation"
        return context


class CentreUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Vue permettant de modifier un centre de formation existant"""
    model = Centre
    permission_required = 'rap_app.change_centre'
    fields = ['nom', 'code_postal']
    template_name = 'centres/centre_form.html'  # ✅ Vérification du chemin correct

    
    def get_context_data(self, **kwargs):
        """
        Ajoute un titre dynamique au contexte en fonction du centre modifié.
        """
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier le centre : {self.object.nom}"
        return context


class CentreDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """Vue permettant de supprimer un centre de formation"""
    model = Centre
    permission_required = 'rap_app.delete_centre'
    success_url = reverse_lazy('centre-list')
    template_name = 'centres/centre_confirm_delete.html'  # ✅ Ajout du bon chemin

