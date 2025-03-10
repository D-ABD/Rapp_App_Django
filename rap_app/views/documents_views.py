from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import  get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect


from ..models import Document, Formation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView


class DocumentListView(BaseListView):
    """Vue listant tous les documents avec options de filtrage"""
    model = Document
    context_object_name = 'documents'
    template_name = 'documents/document_list.html'
    
    def get_queryset(self):
        """
        Récupère la liste des documents avec possibilité de filtrage par:
        - Formation associée
        - Type de document
        - Nom de fichier (recherche textuelle)
        """
        queryset = super().get_queryset().select_related('formation')
        
        # Filtrage par formation
        formation_id = self.request.GET.get('formation')
        if formation_id:
            queryset = queryset.filter(formation_id=formation_id)
            
        # Filtrage par type de document
        type_doc = self.request.GET.get('type_document')
        if type_doc:
            queryset = queryset.filter(type_document=type_doc)
            
        # Recherche textuelle
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(nom_fichier__icontains=q) | 
                Q(source__icontains=q)
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        """Ajout des filtres actuels et des options de filtre au contexte"""
        context = super().get_context_data(**kwargs)
        
        # Filtres actuellement appliqués
        context['filters'] = {
            'formation': self.request.GET.get('formation', ''),
            'type_document': self.request.GET.get('type_document', ''),
            'q': self.request.GET.get('q', ''),
        }
        
        # Liste des formations pour le filtrage
        context['formations'] = Formation.objects.all()
        
        # Types de documents pour le filtrage
        context['types_document'] = Document.TYPE_DOCUMENT_CHOICES
        
        return context
class DocumentDownloadView(BaseDetailView):
    """Vue pour télécharger un document"""
    def get(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        response = HttpResponse(document.fichier, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{document.nom_fichier}"'
        return response
class DocumentDetailView(BaseDetailView):
    """Vue affichant les détails d'un document"""
    model = Document
    context_object_name = 'document'
    template_name = 'documents/document_detail.html'


class DocumentCreateView(PermissionRequiredMixin, BaseCreateView):
    """Vue permettant de créer un nouveau document"""
    model = Document
    permission_required = 'rap_app.add_document'
    fields = ['formation', 'nom_fichier', 'fichier', 'source', 'type_document']
    template_name = 'documents/document_form.html'
    
    def get_initial(self):
        """Pré-remplit le formulaire avec la formation si spécifiée dans l'URL"""
        initial = super().get_initial()
        formation_id = self.request.GET.get('formation')
        if formation_id:
            initial['formation'] = formation_id
        return initial
    
    def get_success_url(self):
        """Redirige vers la formation associée après création"""
        return reverse_lazy('formation-detail', kwargs={'pk': self.object.formation.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter un document"
        # Ajout de la liste des types de documents
        context['types_document'] = Document.TYPE_DOCUMENT_CHOICES
        return context

class DocumentUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Vue permettant de modifier un document existant"""
    model = Document
    permission_required = 'rap_app.change_document'
    fields = ['nom_fichier', 'fichier', 'source', 'type_document']
    template_name = 'documents/document_form.html'
    
    def get_success_url(self):
        """Redirige vers la formation associée après modification"""
        return reverse_lazy('formation-detail', kwargs={'pk': self.object.formation.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier le document : {self.object.nom_fichier}"
        # Ajout de la liste des types de documents
        context['types_document'] = Document.TYPE_DOCUMENT_CHOICES
        return context


class DocumentDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """Vue permettant de supprimer un document"""
    model = Document
    permission_required = 'rap_app.delete_document'
    template_name = 'documents/document_confirm_delete.html'
    
    def get_success_url(self):
        """Redirige vers la formation associée après suppression"""
        formation_id = self.object.formation.id
        return reverse_lazy('formation-detail', kwargs={'pk': formation_id})
    

