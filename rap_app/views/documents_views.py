from django.urls import reverse
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.http import FileResponse, Http404
from django.conf import settings
from django.views.generic import View
import os

from ..models import Document, Formation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView


class DocumentListView(BaseListView):
    """Liste des documents"""
    model = Document
    context_object_name = 'documents'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('formation')
        
        # Filtrer par formation si spécifié
        formation_id = self.request.GET.get('formation')
        if formation_id:
            queryset = queryset.filter(formation_id=formation_id)
        
        # Recherche par nom de fichier
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(nom_fichier__icontains=q)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Formations pour le filtre
        context['formations'] = Formation.objects.formations_actives().order_by('nom')
        
        # Filtres appliqués
        context['filters'] = {
            'formation': self.request.GET.get('formation', ''),
            'q': self.request.GET.get('q', ''),
        }
        
        return context


class DocumentDetailView(BaseDetailView):
    """Détail d'un document"""
    model = Document
    context_object_name = 'document'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer d'autres documents de la même formation
        if self.object.formation:
            context['autres_documents'] = self.object.formation.documents.exclude(
                id=self.object.id
            ).order_by('-created_at')[:5]
        
        return context


class DocumentCreateView(PermissionRequiredMixin, BaseCreateView):
    """Création d'un document"""
    model = Document
    permission_required = 'rap_app.add_document'
    fields = ['formation', 'nom_fichier', 'fichier', 'source']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter un document"
        
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
    
    def get_success_url(self):
        # Si redirigé depuis la vue détaillée d'une formation, y retourner
        if self.object.formation and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': self.object.formation.id})
        return reverse('document-detail', kwargs={'pk': self.object.pk})


class DocumentUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Mise à jour d'un document"""
    model = Document
    permission_required = 'rap_app.change_document'
    fields = ['formation', 'nom_fichier', 'fichier', 'source']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier le document : {self.object.nom_fichier}"
        return context
    
    def get_success_url(self):
        # Si redirigé depuis la vue détaillée d'une formation, y retourner
        if self.object.formation and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': self.object.formation.id})
        return reverse('document-detail', kwargs={'pk': self.object.pk})


class DocumentDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """Suppression d'un document"""
    model = Document
    permission_required = 'rap_app.delete_document'
    
    def get_success_url(self):
        # Rediriger vers la formation si le document est lié à une formation
        formation_id = self.object.formation.id if self.object.formation else None
        if formation_id and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': formation_id})
        return reverse('document-list')


class DocumentDownloadView(View):
    """Vue pour télécharger un document"""
    
    def get(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        
        # Vérifier que l'utilisateur est authentifié
        if not request.user.is_authenticated:
            raise Http404("Document non disponible")
            
        # Construire le chemin du fichier
        file_path = os.path.join(settings.MEDIA_ROOT, document.fichier.name)
        
        # Vérifier que le fichier existe
        if not os.path.exists(file_path):
            messages.error(request, f"Le fichier {document.nom_fichier} n'existe pas")
            return reverse('document-detail', kwargs={'pk': document.pk})
        
        # Ouvrir et retourner le fichier
        try:
            response = FileResponse(open(file_path, 'rb'))
            response['Content-Disposition'] = f'attachment; filename="{document.nom_fichier}"'
            
            # Enregistrer le téléchargement dans l'historique si nécessaire
            # Ajouter votre code ici si vous souhaitez suivre les téléchargements
            
            return response
        except Exception as e:
            messages.error(request, f"Erreur lors du téléchargement : {str(e)}")
            return reverse('document-detail', kwargs={'pk': document.pk})