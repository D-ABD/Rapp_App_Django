from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Count, Sum, Avg, F, Q
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
import csv
import io

from ..models import Rapport, Formation, Centre, TypeOffre, Statut, Evenement, HistoriqueFormation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView


class RapportListView(BaseListView):
    """Liste des rapports"""
    model = Rapport
    context_object_name = 'rapports'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('formation')
        
        # Filtrage par période
        periode = self.request.GET.get('periode')
        if periode:
            queryset = queryset.filter(periode=periode)
        
        # Filtrage par formation
        formation_id = self.request.GET.get('formation')
        if formation_id:
            queryset = queryset.filter(formation_id=formation_id)
        
        # Filtrage par date
        date_debut = self.request.GET.get('date_debut')
        if date_debut:
            queryset = queryset.filter(date_fin__gte=date_debut)
            
        date_fin = self.request.GET.get('date_fin')
        if date_fin:
            queryset = queryset.filter(date_debut__lte=date_fin)
        
        return queryset.order_by('-date_fin')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Données pour les filtres
        context['formations'] = Formation.objects.formations_actives()
        context['periodes'] = Rapport.PERIODE_CHOICES
        
        # Filtres appliqués
        context['filters'] = {
            'periode': self.request.GET.get('periode', ''),
            'formation': self.request.GET.get('formation', ''),
            'date_debut': self.request.GET.get('date_debut', ''),
            'date_fin': self.request.GET.get('date_fin', ''),
        }
        
        return context


class RapportDetailView(BaseDetailView):
    """Détail d'un rapport"""
    model = Rapport
    context_object_name = 'rapport'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer d'autres rapports de la même formation
        if self.object.formation:
            context['autres_rapports'] = self.object.formation.rapports.exclude(
                id=self.object.id
            ).order_by('-date_fin')[:5]
        
        # Calculer quelques statistiques supplémentaires
        context['evolution'] = None
        if self.object.formation:
            # Chercher le rapport précédent pour cette formation et cette période
            rapport_precedent = Rapport.objects.filter(
                formation=self.object.formation,
                periode=self.object.periode,
                date_fin__lt=self.object.date_debut
            ).order_by('-date_fin').first()
            
            if rapport_precedent:
                context['evolution'] = {
                    'inscrits': self.object.total_inscrits - rapport_precedent.total_inscrits,
                    'taux_remplissage': self.object.taux_remplissage - rapport_precedent.taux_remplissage,
                    'rapport_precedent': rapport_precedent
                }
        
        return context


class RapportCreateView(PermissionRequiredMixin, BaseCreateView):
    """Création d'un rapport"""
    model = Rapport
    permission_required = 'rap_app.add_rapport'
    fields = [
        'formation', 'periode', 'date_debut', 'date_fin', 
        'total_inscrits', 'inscrits_crif', 'inscrits_mp', 'total_places',
        'nombre_evenements', 'nombre_candidats', 'nombre_entretiens'
    ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = "Créer un nouveau rapport"
        
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
                
                # Pré-remplir avec les données actuelles de la formation
                form.initial['total_inscrits'] = formation.inscrits_total
                form.initial['inscrits_crif'] = formation.inscrits_crif
                form.initial['inscrits_mp'] = formation.inscrits_mp
                form.initial['total_places'] = formation.total_places
                
                # Essayer de récupérer les données de la ressource
                try:
                    ressource = formation.ressource
                    form.initial['nombre_evenements'] = ressource.nombre_evenements
                    form.initial['nombre_candidats'] = ressource.nombre_candidats
                    form.initial['nombre_entretiens'] = ressource.nombre_entretiens
                except Exception:
                    pass
                
            except Formation.DoesNotExist:
                pass
                
        # Pré-remplir les dates selon la période
        periode = self.request.GET.get('periode')
        now = timezone.now().date()
        
        if periode == Rapport.HEBDOMADAIRE:
            # Semaine précédente (lundi au dimanche)
            start_of_week = now - timedelta(days=now.weekday() + 7)
            end_of_week = start_of_week + timedelta(days=6)
            form.initial['date_debut'] = start_of_week
            form.initial['date_fin'] = end_of_week
            form.initial['periode'] = Rapport.HEBDOMADAIRE
            
        elif periode == Rapport.MENSUEL:
            # Mois précédent
            last_month = now.replace(day=1) - timedelta(days=1)
            start_of_month = last_month.replace(day=1)
            form.initial['date_debut'] = start_of_month
            form.initial['date_fin'] = last_month
            form.initial['periode'] = Rapport.MENSUEL
            
        elif periode == Rapport.ANNUEL:
            # Année précédente
            last_year = now.year - 1
            form.initial['date_debut'] = datetime(last_year, 1, 1).date()
            form.initial['date_fin'] = datetime(last_year, 12, 31).date()
            form.initial['periode'] = Rapport.ANNUEL
        
        return form
    
    def get_success_url(self):
        # Rediriger vers la formation si demandé
        if self.object.formation and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': self.object.formation.id})
        return reverse('rapport-detail', kwargs={'pk': self.object.pk})


class RapportUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Mise à jour d'un rapport"""
    model = Rapport
    permission_required = 'rap_app.change_rapport'
    fields = [
        'formation', 'periode', 'date_debut', 'date_fin', 
        'total_inscrits', 'inscrits_crif', 'inscrits_mp', 'total_places',
        'nombre_evenements', 'nombre_candidats', 'nombre_entretiens'
    ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = f"Modifier le rapport {self.object.get_periode_display()} ({self.object.date_debut} - {self.object.date_fin})"
        return context
    
    def get_success_url(self):
        # Rediriger vers la formation si demandé
        if self.object.formation and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': self.object.formation.id})
        return reverse('rapport-detail', kwargs={'pk': self.object.pk})


class RapportDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """Suppression d'un rapport"""
    model = Rapport
    permission_required = 'rap_app.delete_rapport'
    
    def get_success_url(self):
        # Rediriger vers la formation si le rapport est lié à une formation
        formation_id = self.object.formation.id if self.object.formation else None
        if formation_id and self.request.GET.get('redirect_to_formation') == 'true':
            return reverse('formation-detail', kwargs={'pk': formation_id})
        return reverse('rapport-list')


class RapportGenerationView(LoginRequiredMixin, TemplateView):
    """Vue pour générer des rapports automatiquement"""
    template_name = 'rap_app/rapport_generation.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Options pour le formulaire
        context['formations'] = Formation.objects.formations_actives().order_by('nom')
        context['periodes'] = Rapport.PERIODE_CHOICES
        
        # Type de génération (par période ou par formation)
        context['type_generation'] = self.request.GET.get('type', 'periode')
        
        # Pour la génération par période
        context['periode_selectionnee'] = self.request.GET.get('periode', Rapport.HEBDOMADAIRE)
        
        # Pour la génération par formation
        formation_id = self.request.GET.get('formation')
        if formation_id:
            try:
                context['formation_selectionnee'] = Formation.objects.get(pk=formation_id)
            except Formation.DoesNotExist:
                pass
        
        return context
    
    def post(self, request, *args, **kwargs):
        from django.contrib import messages
        
        # Récupérer les paramètres du formulaire
        type_generation = request.POST.get('type_generation')
        periode = request.POST.get('periode')
        formation_id = request.POST.get('formation')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')
        
        rapports_crees = 0
        
        try:
            # Vérifier que les dates sont valides
            if date_debut and date_fin:
                date_debut = parse_date(date_debut)
                date_fin = parse_date(date_fin)
                
                if date_debut > date_fin:
                    messages.error(request, "La date de début doit être antérieure à la date de fin.")
                    return self.get(request, *args, **kwargs)
            
            # Génération par période (pour toutes les formations)
            if type_generation == 'periode' and periode:
                formations = Formation.objects.formations_actives()
                
                for formation in formations:
                    # Vérifier si un rapport similaire existe déjà
                    rapport_existant = Rapport.objects.filter(
                        formation=formation,
                        periode=periode,
                        date_debut=date_debut,
                        date_fin=date_fin
                    ).exists()
                    
                    if not rapport_existant:
                        # Calculer les valeurs à partir des données existantes
                        nombre_evenements = Evenement.objects.filter(
                            formation=formation,
                            event_date__gte=date_debut,
                            event_date__lte=date_fin
                        ).count()
                        
                        # Créer le rapport
                        Rapport.objects.create(
                            formation=formation,
                            periode=periode,
                            date_debut=date_debut,
                            date_fin=date_fin,
                            total_inscrits=formation.inscrits_total,
                            inscrits_crif=formation.inscrits_crif,
                            inscrits_mp=formation.inscrits_mp,
                            total_places=formation.total_places,
                            nombre_evenements=nombre_evenements,
                            nombre_candidats=getattr(formation.ressource, 'nombre_candidats', 0) or 0,
                            nombre_entretiens=getattr(formation.ressource, 'nombre_entretiens', 0) or 0
                        )
                        rapports_crees += 1
            
            # Génération pour une formation spécifique
            elif type_generation == 'formation' and formation_id:
                formation = get_object_or_404(Formation, pk=formation_id)
                
                # Vérifier si un rapport similaire existe déjà
                rapport_existant = Rapport.objects.filter(
                    formation=formation,
                    periode=periode,
                    date_debut=date_debut,
                    date_fin=date_fin
                ).exists()
                
                if not rapport_existant:
                    # Calculer les valeurs à partir des données existantes
                    nombre_evenements = Evenement.objects.filter(
                        formation=formation,
                        event_date__gte=date_debut,
                        event_date__lte=date_fin
                    ).count()
                    
                    # Créer le rapport
                    Rapport.objects.create(
                        formation=formation,
                        periode=periode,
                        date_debut=date_debut,
                        date_fin=date_fin,
                        total_inscrits=formation.inscrits_total,
                        inscrits_crif=formation.inscrits_crif,
                        inscrits_mp=formation.inscrits_mp,
                        total_places=formation.total_places,
                        nombre_evenements=nombre_evenements,
                        nombre_candidats=getattr(formation.ressource, 'nombre_candidats', 0) or 0,
                        nombre_entretiens=getattr(formation.ressource, 'nombre_entretiens', 0) or 0
                    )
                    rapports_crees += 1
            
            if rapports_crees > 0:
                messages.success(request, f"{rapports_crees} rapport(s) généré(s) avec succès.")
            else:
                messages.info(request, "Aucun nouveau rapport n'a été généré. Peut-être qu'ils existent déjà pour cette période.")
                
        except Exception as e:
            messages.error(request, f"Erreur lors de la génération des rapports : {str(e)}")
        
        return self.get(request, *args, **kwargs)


class RapportExportView(LoginRequiredMixin, View):
    """Vue pour exporter les données des rapports"""
    
    def get(self, request, *args, **kwargs):
        from django.contrib import messages
        
        format_export = request.GET.get('format', 'csv')
        
        # Récupérer les filtres
        periode = request.GET.get('periode')
        formation_id = request.GET.get('formation')
        date_debut = request.GET.get('date_debut')
        date_fin = request.GET.get('date_fin')
        
        # Construire la requête en fonction des filtres
        queryset = Rapport.objects.select_related('formation', 'formation__centre', 'formation__type_offre')
        
        if periode:
            queryset = queryset.filter(periode=periode)
        
        if formation_id:
            queryset = queryset.filter(formation_id=formation_id)
        
        if date_debut:
            queryset = queryset.filter(date_fin__gte=date_debut)
            
        if date_fin:
            queryset = queryset.filter(date_debut__lte=date_fin)
        
        # Ordonner les résultats
        queryset = queryset.order_by('-date_fin')
        
        # Export CSV
        if format_export == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="rapports.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'ID', 'Formation', 'Centre', 'Type d\'offre', 'Période', 
                'Date début', 'Date fin', 'Inscrits CRIF', 'Inscrits MP', 
                'Total inscrits', 'Total places', 'Taux remplissage (%)',
                'Nombre événements', 'Nombre candidats', 'Nombre entretiens',
                'Taux transformation (%)', 'Date création'
            ])
            
            for rapport in queryset:
                writer.writerow([
                    rapport.id,
                    rapport.formation.nom if rapport.formation else 'Global',
                    rapport.formation.centre.nom if rapport.formation and rapport.formation.centre else '-',
                    rapport.formation.type_offre.nom if rapport.formation and rapport.formation.type_offre else '-',
                    rapport.get_periode_display(),
                    rapport.date_debut,
                    rapport.date_fin,
                    rapport.inscrits_crif,
                    rapport.inscrits_mp,
                    rapport.total_inscrits,
                    rapport.total_places,
                    "{:.2f}".format(rapport.taux_remplissage),
                    rapport.nombre_evenements,
                    rapport.nombre_candidats,
                    rapport.nombre_entretiens,
                    "{:.2f}".format(rapport.taux_transformation),
                    rapport.created_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
            
            return response
            
        # Format non pris en charge
        else:
            messages.error(request, f"Format d'export '{format_export}' non pris en charge.")
            return reverse('rapport-list')