from django.db import models

# centres/models.py
class Centre(models.Model):
    nom = models.CharField(max_length=255)
    code_postal = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

# statuts/models.py
class Statut(models.Model):
    nom = models.CharField(max_length=100)
    couleur = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    is_default = models.BooleanField(null=True, blank=True)

# types_offres/models.py
class TypeOffre(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_default = models.BooleanField(null=True, blank=True)

# utilisateurs/models.py
class Utilisateur(models.Model):
    id = models.UUIDField(primary_key=True)
    email = models.EmailField(unique=True)
    nom = models.CharField(max_length=255)
    role = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

# formations/models.py

class Formation(models.Model):
    nom = models.CharField(max_length=255)
    centre = models.ForeignKey('Centre', on_delete=models.CASCADE, related_name="formations")
    type_offre = models.ForeignKey('TypeOffre', on_delete=models.CASCADE, related_name="formations")
    statut = models.ForeignKey('Statut', on_delete=models.CASCADE, related_name="formations")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    num_kairos = models.CharField(max_length=50, null=True, blank=True)
    num_offre = models.CharField(max_length=50, null=True, blank=True)  # Ajouté
    num_produit = models.CharField(max_length=50, null=True, blank=True)
    prevus_crif = models.IntegerField()
    prevus_mp = models.IntegerField()
    total_places = models.IntegerField(null=True, blank=True)
    inscrits_crif = models.IntegerField(default=0)  # Ajouté avec une valeur par défaut
    inscrits_mp = models.IntegerField(default=0)  # Ajouté avec une valeur par défaut
    a_recruter = models.IntegerField(default=0)  # Ajouté avec une valeur par défaut
    assistante = models.CharField(max_length=255, null=True, blank=True)  # Ajouté
    cap = models.IntegerField(null=True, blank=True)  # Ajouté
    convocation_envoie = models.BooleanField(default=False)  # Ajouté
    entresformation = models.IntegerField(default=0, verbose_name="Entrées en formation")

    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom


# commentaires/models.py
class Commentaire(models.Model):
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name="commentaires")
    auteur = models.CharField(max_length=255)
    contenu = models.TextField()
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name="commentaires")
    created_at = models.DateTimeField(auto_now_add=True)

# documents/models.py
class Document(models.Model):
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name="documents")
    nom_fichier = models.CharField(max_length=255)
    url = models.URLField()
    source = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

# evenements/models.py
class Evenement(models.Model):
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, null=True, blank=True, related_name="evenements")
    type_evenement = models.CharField(max_length=100)
    details = models.TextField(null=True, blank=True)
    event_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

# historique/models.py
class HistoriqueFormation(models.Model):
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, null=True, blank=True, related_name="historique_formations")
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name="historique_utilisateurs")
    action = models.CharField(max_length=255)
    ancien_statut = models.CharField(max_length=100, null=True, blank=True)
    nouveau_statut = models.CharField(max_length=100, null=True, blank=True)
    details = models.JSONField(null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

# ressources/models.py
class Ressource(models.Model):
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, null=True, blank=True, related_name="ressources")
    nombre_candidats = models.IntegerField(null=True, blank=True)
    nombre_entretiens = models.IntegerField(null=True, blank=True)
    nombre_evenements = models.IntegerField(null=True, blank=True)
    taux_transformation = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

# parametres/models.py
class Parametre(models.Model):
    cle = models.CharField(max_length=100, unique=True)
    valeur = models.TextField()
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
