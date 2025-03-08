from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages


class BaseListView(LoginRequiredMixin, ListView):
    """Vue de base pour les listes avec pagination"""
    paginate_by = 20
    template_name_suffix = '_list'


class BaseDetailView(LoginRequiredMixin, DetailView):
    """Vue de base pour afficher un détail"""
    template_name_suffix = '_detail'


class BaseCreateView(LoginRequiredMixin, CreateView):
    """Vue de base pour créer un objet"""

    def form_valid(self, form):
        """Ajoute un message de succès après la création"""
        response = super().form_valid(form)
        messages.success(self.request, f"{self.model._meta.verbose_name} créé avec succès.")
        return response


class BaseUpdateView(LoginRequiredMixin, UpdateView):
    """Vue de base pour modifier un objet"""

    def form_valid(self, form):
        """Ajoute un message de succès après la modification"""
        response = super().form_valid(form)
        messages.success(self.request, f"{self.model._meta.verbose_name} mis à jour avec succès.")
        return response


class BaseDeleteView(LoginRequiredMixin, DeleteView):
    """Vue de base pour supprimer un objet"""
    success_url = reverse_lazy('dashboard')

    def delete(self, request, *args, **kwargs):
        """Ajoute un message de succès après la suppression"""
        messages.success(request, f"{self.model._meta.verbose_name} supprimé avec succès.")
        return super().delete(request, *args, **kwargs)
