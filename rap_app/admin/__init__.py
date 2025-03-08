"""
Importe les classes admin pour l'interface d'administration Django.
L'importation des classes admin enregistre automatiquement les modèles avec admin.site.
"""

from .centres_admin import CentreAdmin
from .statuts_admin import StatutAdmin
from .types_offre_admin import TypeOffreAdmin
from .formations_admin import FormationAdmin
from .commentaires_admin import CommentaireAdmin
from .historiques_formations_admin import HistoriqueFormationAdmin
from .rapports_admin import RapportAdmin
from .parametres_admin import ParametreAdmin
from .recherches_admin import RechercheAdmin
from .entreprises_admin import EntrepriseAdmin  # Nouveau
from .evenements_admin import EvenementAdmin    # Nouveau
from .documents_admin import DocumentAdmin      # Nouveau

