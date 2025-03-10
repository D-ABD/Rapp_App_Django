from urllib import request
from django.urls import reverse_lazy
from django.db.models import Q, F, ExpressionWrapper, IntegerField, FloatField
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect


from django.contrib import messages
from django.http import HttpResponseBadRequest

from ..models.entreprises import Entreprise
from ..models import Formation


from ..models.centres import Centre
from ..models.statut import Statut
from ..models.types_offre import TypeOffre

from ..models.commentaires import Commentaire
from ..models import Formation, HistoriqueFormation
from .base_views import BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView


class FormationListView(BaseListView):
    """Vue listant toutes les formations avec options de filtrage et indicateurs dynamiques."""
    model = Formation
    context_object_name = 'formations'
    template_name = 'formations/formation_list.html'
    paginate_by = 10  # ✅ Ajout de la pagination

    def get_queryset(self):
        """
        Récupère la liste des formations avec :
        - Affichage de toutes les formations par défaut
        - Filtrage par statut, type d'offre, centre si l'utilisateur sélectionne un filtre
        - Calcul dynamique des indicateurs : total_places, taux_saturation, etc.
        """
        today = timezone.now().date()

        queryset = Formation.objects.select_related('centre', 'type_offre', 'statut').annotate(
            total_places=ExpressionWrapper(
                F('prevus_crif') + F('prevus_mp'), output_field=IntegerField()
            ),
            total_inscrits=ExpressionWrapper(
                F('inscrits_crif') + F('inscrits_mp'), output_field=IntegerField()
            ),
            places_restantes_crif=ExpressionWrapper(
                F('prevus_crif') - F('inscrits_crif'), output_field=IntegerField()
            ),
            places_restantes_mp=ExpressionWrapper(
                F('prevus_mp') - F('inscrits_mp'), output_field=IntegerField()
            ),
            taux_saturation=ExpressionWrapper(
                100.0 * (F('inscrits_crif') + F('inscrits_mp')) / 
                (F('prevus_crif') + F('prevus_mp')), output_field=FloatField()
            ),
            
            
        )  # ✅ On n'applique plus de filtre par défaut

        print("Formations récupérées avant filtrage :", queryset)  # ✅ Debug

        # 🔍 Application des filtres SEULEMENT si une valeur est sélectionnée
        centre_id = self.request.GET.get('centre', '').strip()
        type_offre_id = self.request.GET.get('type_offre', '').strip()
        statut_id = self.request.GET.get('statut', '').strip()
        periode = self.request.GET.get('periode', '').strip()

        if centre_id:
            queryset = queryset.filter(centre_id=centre_id)
        if type_offre_id:
            queryset = queryset.filter(type_offre_id=type_offre_id)
        if statut_id:
            queryset = queryset.filter(statut_id=statut_id)
        if periode:
            if periode == 'active':
                queryset = queryset.filter(start_date__lte=today, end_date__gte=today)
            elif periode == 'a_venir':
                queryset = queryset.filter(start_date__gt=today)
            elif periode == 'terminee':
                queryset = queryset.filter(end_date__lt=today)
            elif periode == 'a_recruter':
                queryset = queryset.filter(total_places__gt=F('total_inscrits'))

        print("Formations après filtrage :", queryset)  # ✅ Debug

        return queryset  # ✅ Retourne toutes les formations si aucun filtre n'est appliqué

    def get_context_data(self, **kwargs):
        """Ajoute les statistiques, les centres, types d'offres et statuts au contexte pour le template."""
        context = super().get_context_data(**kwargs)

        context['stats'] = [
            (Formation.objects.count(), "Total", "primary"),
            (Formation.objects.formations_actives().count(), "Actives", "success"),
            (Formation.objects.formations_a_venir().count(), "À venir", "info"),
            (Formation.objects.formations_terminees().count(), "Terminées", "secondary"),
            (Formation.objects.formations_a_recruter().count(), "À recruter", "warning"),
        ]

        # ✅ Ajout des données pour les filtres
        context['centres'] = Centre.objects.all()
        context['types_offre'] = TypeOffre.objects.all()
        context['statuts'] = Statut.objects.all()

        # ✅ Ajout des filtres actifs pour ne pas les perdre après soumission
        context['filters'] = {
            'centre': self.request.GET.get('centre', ''),
            'type_offre': self.request.GET.get('type_offre', ''),
            'statut': self.request.GET.get('statut', ''),
            'periode': self.request.GET.get('periode', ''),
        }
# Ajout des noms de colonnes pour l'affichage
        context['colonnes'] = [
            {'nom': 'Nom', 'field': 'nom'},
            {'nom': 'Centre', 'field': 'centre__nom'},
            {'nom': 'Type', 'field': 'type_offre__nom'},
            {'nom': 'Statut', 'field': 'statut__nom'},
            {'nom': 'N° Offre', 'field': 'num_offre'},
            {'nom': 'Début', 'field': 'start_date'},
            {'nom': 'Fin', 'field': 'end_date'},
            {'nom': 'Places CRIF', 'field': 'places_restantes_crif'},
            {'nom': 'Places MP', 'field': 'places_restantes_mp'},
            {'nom': 'Total places', 'field': 'total_places'},
            {'nom': 'Disponibles', 'field': 'places_disponibles'},
            {'nom': 'Saturation (%)', 'field': 'taux_saturation'},
        ]
        return context


class FormationDetailView(BaseDetailView):
    """Vue affichant les détails d'une formation"""
    model = Formation
    context_object_name = 'formation'
    template_name = 'formations/formation_detail.html'

    def get_context_data(self, **kwargs):
        """Ajoute les commentaires, evenements et autres données au contexte"""
        context = super().get_context_data(**kwargs)
        formation = self.object

    # Récupération du dernier commentaire avec toutes ses infos
        dernier_commentaire = formation.get_commentaires().order_by('-created_at').first()

    # ✅ Entreprises associées
        context['entreprises'] = formation.entreprises.all()

        # ✅ Entreprises disponibles (celles qui ne sont pas encore associées)
        context['entreprises_disponibles'] = Entreprise.objects.exclude(id__in=formation.entreprises.values_list('id', flat=True))


        context['dernier_commentaire'] = dernier_commentaire  # ✅ Ajout du dernier commentaire complet
        context['commentaires'] = formation.get_commentaires().order_by('-created_at')
        context['evenements'] = formation.get_evenements().order_by('-event_date')
        context['documents'] = formation.documents.all().order_by('-created_at')
        context['entreprises'] = formation.get_entreprises()
        context['historique'] = formation.historique_formations.order_by('-created_at')[:10]

        # ✅ Ajout des valeurs calculées pour affichage
        context['places_restantes_crif'] = formation.get_places_restantes_crif()
        context['places_restantes_mp'] = formation.get_places_restantes_mp()
        context['taux_saturation'] = formation.get_taux_saturation()

        return context
    
    def post(self, request, *args, **kwargs):
            """
            Gère l'ajout de commentaires, événements, documents et entreprises via POST.
            L'action est déterminée par le champ `action` du formulaire.
            """
            formation = self.get_object()
            action = request.POST.get('action')

            if action == 'add_commentaire':
                return self.add_commentaire(request, formation)

            elif action == 'add_evenement':
                return self.add_evenement(request, formation)

            elif action == 'add_document':
                return self.add_document(request, formation)

            elif action == 'add_entreprise':
                return self.add_entreprise(request, formation)

            return HttpResponseBadRequest("Action non valide.")

    def add_commentaire(self, request, formation):
        """Ajoute un commentaire à la formation"""
        contenu = request.POST.get('contenu', '').strip()

        if not contenu:
            return HttpResponseBadRequest("Le commentaire ne peut pas être vide.")

        formation.add_commentaire(request.user, contenu)
        messages.success(request, "Commentaire ajouté avec succès.")
        return redirect(self.request.path)

    def add_evenement(self, request, formation):
        """Ajoute un événement à la formation"""
        type_evenement = request.POST.get('type_evenement', '').strip()
        date = request.POST.get('date')
        details = request.POST.get('details', '').strip()
        description_autre = request.POST.get('description_autre', '').strip()

        if not type_evenement or not date:
            return HttpResponseBadRequest("Le type et la date de l'événement sont obligatoires.")

    # ✅ On appelle la méthode avec les bons arguments (4 au total)
        formation.add_evenement(type_evenement, date, details, description_autre)
        messages.success(request, "Événement ajouté avec succès.")
        return redirect(self.request.path)

    def add_document(self, request, formation):
        """Ajoute un document à la formation."""
        nom = request.POST.get('nom', '').strip()
        fichier = request.FILES.get('fichier')

        if not nom or not fichier:
            return HttpResponseBadRequest("Le nom et le fichier sont obligatoires.")

        # ✅ Ajout du document directement avec `.create()`
        formation.documents.create(
            utilisateur=request.user, 
            nom_fichier=nom, 
            fichier=fichier
        )

        messages.success(request, "Document ajouté avec succès.")
        return redirect(self.request.path)

class FormationCreateView(PermissionRequiredMixin, BaseCreateView):
    """Vue permettant de créer une nouvelle formation"""
    model = Formation
    permission_required = 'rap_app.add_formation'
    template_name = 'formations/formation_form.html'
    fields = [
        'nom', 'centre', 'type_offre', 'statut', 'start_date', 'end_date',
        'num_kairos', 'num_offre', 'num_produit', 'prevus_crif', 'prevus_mp',
        'inscrits_crif', 'inscrits_mp', 'assistante', 'cap', 'convocation_envoie',
        'entresformation', 'nombre_candidats', 'nombre_entretiens'
    ]

    def form_valid(self, form):
        """Associe l'utilisateur connecté à la formation et crée un historique"""
        with transaction.atomic():
            form.instance.utilisateur = self.request.user
            response = super().form_valid(form)

            # 📌 Création d'un historique
            HistoriqueFormation.objects.create(
                formation=self.object,
                utilisateur=self.request.user,
                action='création',
                details={'nom': self.object.nom}
            )

            return response

    def get_success_url(self):
        return reverse_lazy('formation-detail', kwargs={'pk': self.object.pk})


class FormationUpdateView(PermissionRequiredMixin, BaseUpdateView):
    """Vue permettant de modifier une formation existante"""
    model = Formation
    permission_required = 'rap_app.change_formation'
    template_name = 'formations/formation_form.html'
    fields = FormationCreateView.fields  # ✅ Réutilisation des champs

    def form_valid(self, form):
        """Détecte les modifications et met à jour l'historique"""
        with transaction.atomic():
            old_obj = Formation.objects.get(pk=self.object.pk)
            response = super().form_valid(form)

            # ✅ Comparaison des champs modifiés
            changes = {}
            for field in self.fields:
                old_value, new_value = getattr(old_obj, field), getattr(self.object, field)
                if old_value != new_value:
                    changes[field] = {'ancien': old_value, 'nouveau': new_value}

            # 📌 Enregistre l'historique si des changements ont été détectés
            if changes:
                HistoriqueFormation.objects.create(
                    formation=self.object,
                    utilisateur=self.request.user,
                    action='modification',
                    details=changes
                )

            return response

    def get_success_url(self):
        return reverse_lazy('formation-detail', kwargs={'pk': self.object.pk})


class FormationDeleteView(PermissionRequiredMixin, BaseDeleteView):
    """Vue permettant de supprimer une formation"""
    model = Formation
    permission_required = 'rap_app.delete_formation'
    success_url = reverse_lazy('formation-list')
    template_name = 'formations/formation_confirm_delete.html'


class FormationAddCommentView(BaseCreateView):
    """Vue permettant d'ajouter un commentaire à une formation"""
    model = Commentaire
    fields = ['contenu']
    template_name = 'formations/formation_add_comment.html'

    def dispatch(self, request, *args, **kwargs):
        """Vérifie que la formation existe avant d'ajouter un commentaire"""
        self.formation = get_object_or_404(Formation, pk=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Associe le commentaire à la formation et à l'utilisateur"""
        form.instance.formation = self.formation
        form.instance.utilisateur = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('formation-detail', kwargs={'pk': self.formation.pk})
