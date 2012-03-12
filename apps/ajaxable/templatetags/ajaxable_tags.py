from django import template
from ajaxable.utils import placeholdized
register = template.Library()

@register.filter
def placeholdize(form):
    return placeholdized(form)
