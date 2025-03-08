from django.urls import reverse_lazy
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect

from ..models import Parametre
from .base_views import BaseListView, BaseUpdateView


class ParametreListView(PermissionRequiredMixin, BaseListView):
    """Liste des paramètres de l'application"""
    model = Parametre
    context_object_name = 'parametres'
    permission_required = 'rap_app.view_parametre'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Recherche par clé ou valeur
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(cle__icontains=q) | queryset.filter(valeur__icontains=q)
            
        return queryset.order_by('cle')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filtres appliqués
        context['filters'] = {
            'q': self.request.GET.get('q', ''),
        }
        
        return context


class ParametreUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Mise à jour d'un paramètre"""
    model = Parametre
    fields = ['valeur', 'description']
    permission_required = 'rap_app.change_parametre'
    success_url = reverse_lazy('parametre-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier le paramètre : {self.object.cle}"
        return context
    
    def form_valid(self, form):
        messages.success(self.request, f"Paramètre '{self.object.cle}' mis à jour avec succès.")
        return super().form_valid(form)


class ParametreBatchCreateView(PermissionRequiredMixin, BaseListView):
    """Vue pour créer des paramètres par lot"""
    model = Parametre
    template_name = 'rap_app/parametre_batch_create.html'
    permission_required = 'rap_app.add_parametre'
    
    def post(self, request, *args, **kwargs):
        # Récupérer les paramètres prédéfinis
        parametres_predefinies = {
            'APP_NAME': 'RAP - Recrutement et Accès à la Profession',
            'EMAIL_CONTACT': 'contact@example.com',
            'LIMITE_PAGINATION': '20',
            'ALERTE_TAUX_REMPLISSAGE_FAIBLE': '50',
            'ALERTE_TAUX_REMPLISSAGE_MOYEN': '75',
            'ALERTE_TAUX_REMPLISSAGE_ELEVE': '90',
            'PERIODE_RAPPORT_PAR_DEFAUT': 'Mensuel',
            'LIMITE_EVENEMENTS_PAR_PAGE': '10',
            'LIMITE_COMMENTAIRES_PAR_PAGE': '10',
            'DATE_FORMAT': 'Y-m-d',
            'DATETIME_FORMAT': 'Y-m-d H:i:s',
        }
        
        # Paramètres créés
        crees = 0
        
        # Créer les paramètres manquants
        for cle, valeur in parametres_predefinies.items():
            if not Parametre.objects.filter(cle=cle).exists():
                Parametre.objects.create(
                    cle=cle,
                    valeur=valeur,
                    description=f"Paramètre {cle} créé automatiquement"
                )
                crees += 1
        
        if crees > 0:
            messages.success(request, f"{crees} paramètre(s) ajouté(s) avec succès.")
        else:
            messages.info(request, "Tous les paramètres prédéfinis existent déjà.")
            
        return redirect('parametre-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter des paramètres prédéfinis"
        return context