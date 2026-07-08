# publications/templatetags/json_extras.py
import json
from django import template

register = template.Library()

@register.filter
def json_loads(value):
    try:
        return json.loads(value)
    except:
        return []
