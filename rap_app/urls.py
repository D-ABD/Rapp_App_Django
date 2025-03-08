from django.urls import path

from .views import home_views, centres_views, statuts_views, types_offre_views  # Import des vues

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
]
