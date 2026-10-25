from django import template
from django.http import QueryDict

register = template.Library()


@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    """
    Returns an encoded URL query string that preserves existing GET parameters
    while updating or setting specified parameters.

    Example usage in templates:
        href="{% query_transform page=page_obj.next_page_number %}"
        href="{% query_transform page=1 %}"
    """
    request = context.get("request")
    if request and hasattr(request, "GET"):
        query_dict = request.GET.copy()
    else:
        query_dict = QueryDict(mutable=True)

    for key, value in kwargs.items():
        if value is None or value == "":
            query_dict.pop(key, None)
        elif isinstance(value, (list, tuple)):
            query_dict.setlist(key, [str(v) for v in value])
        else:
            query_dict[key] = str(value)

    encoded = query_dict.urlencode()
    return f"?{encoded}" if encoded else "?"

