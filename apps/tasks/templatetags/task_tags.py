from django import template

register = template.Library()

_STATUS_CLASSES = {
    'new': 'bg-secondary',
    'inprogress': 'bg-primary',
    'review': 'bg-warning text-dark',
    'workerdone': 'bg-info text-dark',
    'headdone': 'bg-success',
    'cancel': 'bg-danger',
}

_PRIORITY_CLASSES = {
    'low': 'bg-secondary',
    'normal': 'bg-primary',
    'high': 'bg-warning text-dark',
    'urgent': 'bg-danger',
}


@register.filter
def status_class(status):
    return _STATUS_CLASSES.get(status, 'bg-secondary')


@register.filter
def priority_class(priority):
    return _PRIORITY_CLASSES.get(priority, 'bg-secondary')
