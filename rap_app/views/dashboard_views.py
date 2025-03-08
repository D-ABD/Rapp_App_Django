from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum, Avg, F, Q, Case, When, IntegerField, Value
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta

from ..models import Formation, Centre, TypeOffre, Statut, Evenement, HistoriqueFormation, Recherche


class DashboardView(LoginRequiredMixin, TemplateView):
    """Vue du tableau de bord principal"""
    template_name = 'rap_app/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques globales
        context['total_formations'] = Formation.objects.count()
        context['formations_actives'] = Formation.objects.formations_actives().count()
        context['formations_a_venir'] = Formation.objects.formations_a_venir().count()
        
        # Formations par statut
        statuts = Statut.objects.annotate(
            nb_formations=Count('formations')
        ).filter(nb_formations__gt=0).order_by('-nb_formations')
        
        context['statuts'] = statuts
        
        # Taux de remplissage moyen des formations actives
        from django.db.models.functions import Coalesce
        
        taux_remplissage = Formation.objects.formations_actives().aggregate(
            taux=Avg(
                100 * (F('inscrits_crif') + F('inscrits_mp')) / 
                Coalesce(F('prevus_crif') + F('prevus_mp'), Value(1), output_field=IntegerField())
            )
        )
        
        context['taux_remplissage_moyen'] = taux_remplissage['taux'] or 0
        
        # Formations récentes
        context['formations_recentes'] = Formation.objects.select_related(
            'centre', 'type_offre', 'statut'
        ).order_by('-created_at')[:5]
        
        # Événements à venir
        context['evenements_a_venir'] = Evenement.objects.select_related(
            'formation'
        ).filter(
            event_date__gte=timezone.now().date()
        ).order_by('event_date')[:5]
        
        # Récentes recherches (pour administrateurs)
        if self.request.user.is_staff:
            context['recherches_recentes'] = Recherche.objects.select_related(
                'utilisateur'
            ).order_by('-created_at')[:10]
        
        return context


class StatsAPIView(LoginRequiredMixin, TemplateView):
    """API pour les données statistiques"""
    
    def get(self, request, *args, **kwargs):
        action = request.GET.get('action')
        
        if action == 'formations_par_statut':
            return self.formations_par_statut()
        elif action == 'evolution_formations':
            return self.evolution_formations()
        elif action == 'formations_par_type':
            return self.formations_par_type()
        elif action == 'taux_remplissage':
            return self.taux_remplissage()
        else:
            return JsonResponse({'error': 'Action non reconnue'}, status=400)
    
    def formations_par_statut(self):
        """Renvoie le nombre de formations par statut"""
        from django.db.models.functions import Coalesce
        
        statuts = Statut.objects.annotate(
            nb_formations=Count('formations'),
            taux_moyen=Coalesce(
                Avg(
                    100 * (F('formations__inscrits_crif') + F('formations__inscrits_mp')) / 
                    Coalesce(F('formations__prevus_crif') + F('formations__prevus_mp'), Value(1), output_field=IntegerField())
                ),
                0
            )
        ).values('nom', 'nb_formations', 'taux_moyen', 'couleur')
        
        return JsonResponse({
            'statuts': list(statuts)
        })
    
    def evolution_formations(self):
        """Renvoie l'évolution du nombre de formations et d'inscrits par mois"""
        from django.db.models.functions import TruncMonth
        
        # Historique des 12 derniers mois
        date_limite = timezone.now().date() - timedelta(days=365)
        
        evolution = HistoriqueFormation.objects.filter(
            created_at__gte=date_limite
        ).annotate(
            mois=TruncMonth('created_at')
        ).values('mois').annotate(
            nb_inscrits=Sum('inscrits_total'),
            nb_formations=Count('formation', distinct=True)
        ).order_by('mois')
        
        # Convertir les dates en chaînes pour JSON
        for item in evolution:
            if item['mois']:
                item['mois'] = item['mois'].strftime('%Y-%m')
        
        return JsonResponse({
            'evolution': list(evolution)
        })
    
    def formations_par_type(self):
        """Renvoie le nombre de formations par type d'offre"""
        types = TypeOffre.objects.annotate(
            nb_formations=Count('formations')
        ).filter(nb_formations__gt=0).values('nom', 'nb_formations')
        
        return JsonResponse({
            'types': list(types)
        })
    
    def taux_remplissage(self):
        """Renvoie le taux de remplissage des formations actives"""
        from django.db.models.functions import Coalesce
        
        formations = Formation.objects.formations_actives().annotate(
            taux=100 * (F('inscrits_crif') + F('inscrits_mp')) / 
                Coalesce(F('prevus_crif') + F('prevus_mp'), Value(1), output_field=IntegerField())
        ).values('id', 'nom', 'taux')
        
        # Calculer la répartition par tranches
        tranches = {
            '0-25%': 0,
            '25-50%': 0,
            '50-75%': 0,
            '75-100%': 0,
            '>100%': 0
        }
        
        for f in formations:
            taux = f['taux']
            if taux <= 25:
                tranches['0-25%'] += 1
            elif taux <= 50:
                tranches['25-50%'] += 1
            elif taux <= 75:
                tranches['50-75%'] += 1
            elif taux <= 100:
                tranches['75-100%'] += 1
            else:
                tranches['>100%'] += 1
        
        return JsonResponse({
            'formations': list(formations),
            'tranches': tranches
        })