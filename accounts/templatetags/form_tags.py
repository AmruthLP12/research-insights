from django import template

register = template.Library()


@register.filter(name="add_class")
def add_class(value, css_class):
    """Append or set CSS class on a bound form field."""
    if hasattr(value, "as_widget"):
        existing_classes = value.field.widget.attrs.get("class", "")
        new_classes = f"{existing_classes} {css_class}".strip() if existing_classes else css_class
        return value.as_widget(attrs={"class": new_classes})
    return value

