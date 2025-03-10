"""
Vue de l'application RAP (Recrutement et Accès à la Profession).
Ce module contient toutes les vues de l'application organisées par modèle.
"""

from .base_views import (
    BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, BaseDeleteView
)



from .centres_views import (
    CentreListView, CentreDetailView, CentreCreateView, 
    CentreUpdateView, CentreDeleteView
)

from .evenements_views import (
    EvenementListView, EvenementDetailView, EvenementCreateView, 
    EvenementUpdateView, EvenementDeleteView
)

from .commentaires_views import (
    CommentaireListView, CommentaireDetailView, CommentaireCreateView, 
    CommentaireUpdateView, CommentaireDeleteView
)

from .documents_views import (
    DocumentListView, DocumentDetailView, DocumentCreateView, 
    DocumentUpdateView, DocumentDeleteView, DocumentDownloadView
)

from .rapport_views import (
    RapportListView, RapportDetailView, RapportCreateView, 
    RapportUpdateView, RapportDeleteView, RapportGenerationView, 
    RapportExportView
)

from .dashboard_views import (
    DashboardView, StatsAPIView
)

from .statuts_views import (
    StatutListView, StatutDetailView, StatutCreateView,
    StatutUpdateView, StatutDeleteView
)

from .types_offre_views import (
    TypeOffreListView, TypeOffreDetailView, TypeOffreCreateView,
    TypeOffreUpdateView, TypeOffreDeleteView
)


from .documents_views import DocumentDownloadView



from .historique_formations_views import (
    HistoriqueFormationListView, HistoriqueFormationDetailView
)



from .parametres_views import (
    ParametreListView, ParametreUpdateView
)