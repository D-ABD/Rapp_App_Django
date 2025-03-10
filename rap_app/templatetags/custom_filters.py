
from django import template

register = template.Library()

@register.filter
def get_value(queryset, key):
    """Retourne l'objet correspondant à la clé donnée."""
    return queryset.filter(id=key).first()
