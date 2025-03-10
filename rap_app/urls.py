from django.urls import path

from .views import (
    home_views, centres_views, statuts_views, types_offre_views,
    commentaires_views, documents_views, entreprises_views, evenements_views, formations_views
)  # Import des vues

urlpatterns = [
    # Page d'accueil
    path('', home_views.home, name='home'),

    # Centres de formation
    path('centres/', centres_views.CentreListView.as_view(), name='centre-list'),
    path('centres/<int:pk>/', centres_views.CentreDetailView.as_view(), name='centre-detail'),
    path('centres/ajouter/', centres_views.CentreCreateView.as_view(), name='centre-create'),
    path('centres/<int:pk>/modifier/', centres_views.CentreUpdateView.as_view(), name='centre-update'),
    path('centres/<int:pk>/supprimer/', centres_views.CentreDeleteView.as_view(), name='centre-delete'),

    # Statuts des formations
    path('statuts/', statuts_views.StatutListView.as_view(), name='statut-list'),
    path('statuts/<int:pk>/', statuts_views.StatutDetailView.as_view(), name='statut-detail'),
    path('statuts/ajouter/', statuts_views.StatutCreateView.as_view(), name='statut-create'),
    path('statuts/<int:pk>/modifier/', statuts_views.StatutUpdateView.as_view(), name='statut-update'),
    path('statuts/<int:pk>/supprimer/', statuts_views.StatutDeleteView.as_view(), name='statut-delete'),

    # Types d'offres
    path('types-offres/', types_offre_views.TypeOffreListView.as_view(), name='type-offre-list'),
    path('types-offres/<int:pk>/', types_offre_views.TypeOffreDetailView.as_view(), name='type-offre-detail'),
    path('types-offres/ajouter/', types_offre_views.TypeOffreCreateView.as_view(), name='type-offre-create'),
    path('types-offres/<int:pk>/modifier/', types_offre_views.TypeOffreUpdateView.as_view(), name='type-offre-update'),
    path('types-offres/<int:pk>/supprimer/', types_offre_views.TypeOffreDeleteView.as_view(), name='type-offre-delete'),

    # Commentaires
    path('commentaires/', commentaires_views.CommentaireListView.as_view(), name='commentaire-list'),
    path('commentaires/<int:pk>/', commentaires_views.CommentaireDetailView.as_view(), name='commentaire-detail'),
    path('commentaires/ajouter/', commentaires_views.CommentaireCreateView.as_view(), name='commentaire-create'),
    path('commentaires/<int:pk>/modifier/', commentaires_views.CommentaireUpdateView.as_view(), name='commentaire-update'),
    path('commentaires/<int:pk>/supprimer/', commentaires_views.CommentaireDeleteView.as_view(), name='commentaire-delete'),
    
    # Documents
    path('documents/', documents_views.DocumentListView.as_view(), name='document-list'),
    path('documents/<int:pk>/', documents_views.DocumentDetailView.as_view(), name='document-detail'),
    path('documents/ajouter/', documents_views.DocumentCreateView.as_view(), name='document-create'),
    path('documents/ajouter/<int:formation_id>/', documents_views.DocumentCreateView.as_view(), name='document-create-formation'),

    path('documents/<int:pk>/modifier/', documents_views.DocumentUpdateView.as_view(), name='document-update'),
    path('documents/<int:pk>/supprimer/', documents_views.DocumentDeleteView.as_view(), name='document-delete'),
    
    # Entreprises
    path('entreprises/', entreprises_views.EntrepriseListView.as_view(), name='entreprise-list'),
    path('entreprises/<int:pk>/', entreprises_views.EntrepriseDetailView.as_view(), name='entreprise-detail'),
    path('entreprises/ajouter/', entreprises_views.EntrepriseCreateView.as_view(), name='entreprise-create'),
    path('entreprises/<int:pk>/modifier/', entreprises_views.EntrepriseUpdateView.as_view(), name='entreprise-update'),
    path('entreprises/<int:pk>/supprimer/', entreprises_views.EntrepriseDeleteView.as_view(), name='entreprise-delete'),
    path('entreprises/ajouter/formation/<int:formation_id>/', entreprises_views.EntrepriseCreateViewFormation.as_view(), name='entreprise-add-formation'),

    # Événements
    path('evenements/', evenements_views.EvenementListView.as_view(), name='evenement-list'),
    path('evenements/<int:pk>/', evenements_views.EvenementDetailView.as_view(), name='evenement-detail'),
    path('evenements/ajouter/', evenements_views.EvenementCreateView.as_view(), name='evenement-create'),
    path('evenements/<int:pk>/modifier/', evenements_views.EvenementUpdateView.as_view(), name='evenement-update'),
    path('evenements/<int:pk>/supprimer/', evenements_views.EvenementDeleteView.as_view(), name='evenement-delete'),
    
    # Formations
    path('formations/', formations_views.FormationListView.as_view(), name='formation-list'),
    path('formations/<int:pk>/', formations_views.FormationDetailView.as_view(), name='formation-detail'),
    path('formations/ajouter/', formations_views.FormationCreateView.as_view(), name='formation-create'),
    path('formations/<int:pk>/modifier/', formations_views.FormationUpdateView.as_view(), name='formation-update'),
    path('formations/<int:pk>/supprimer/', formations_views.FormationDeleteView.as_view(), name='formation-delete'),
    path('formations/<int:pk>/commentaire/', formations_views.FormationAddCommentView.as_view(), name='formation-add-comment'),
]