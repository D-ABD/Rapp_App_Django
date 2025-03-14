# Generated by Django 4.2.7 on 2025-03-08 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rap_app', '0004_delete_ressource'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='entreprise',
            name='rap_app_ent_est_act_c3aa9b_idx',
        ),
        migrations.RemoveField(
            model_name='entreprise',
            name='est_active',
        ),
        migrations.RemoveField(
            model_name='entreprise',
            name='est_visible_dans_formation',
        ),
        migrations.AddField(
            model_name='formation',
            name='nombre_candidats',
            field=models.PositiveIntegerField(default=0, verbose_name='Nombre de candidats'),
        ),
        migrations.AddField(
            model_name='formation',
            name='nombre_entretiens',
            field=models.PositiveIntegerField(default=0, verbose_name="Nombre d'entretiens"),
        ),
        migrations.AddField(
            model_name='formation',
            name='nombre_evenements',
            field=models.PositiveIntegerField(default=0, verbose_name="Nombre d'événements"),
        ),
    ]
