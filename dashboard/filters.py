import django_filters
from django import forms

from django.db.models import Q

from publications.models import Department, Publication


# Your default Tailwind class (example – adjust to yours)
DEFAULT_FILTER_CLASSES = (
    "w-full px-3 py-2 rounded-lg border border-border bg-surface text-text "
    "placeholder-text-muted shadow-sm transition duration-200 "
    "focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-primary-400 "
    "dark:bg-surface-dark dark:border-border-dark dark:text-text-dark "
    "dark:placeholder-text-muted-dark"
)

SELECT_CLASSES = (
    "block w-full px-4 py-3.5 border border-border rounded-xl bg-surface "
    "text-text focus:ring-2 focus:ring-primary-500 focus:border-primary-500 "
    "focus:outline-none transition-all duration-200 hover:border-primary-300 "
    "shadow-sm focus:shadow-md cursor-pointer"
)


class DynamicFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        method="search_filter",
        label="Search",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter search term...",
                "class": DEFAULT_FILTER_CLASSES,
            }
        ),
    )

    INTERNAL_FILTERS = {"ordering"}

    def __init__(self, data=None, queryset=None, *, view=None, **kwargs):
        dynamic_filters = {}

        exact_filters = getattr(view, "exact_filters", [])
        gt_filters = getattr(view, "gt_filters", [])
        lt_filters = getattr(view, "lt_filters", [])
        sortable_fields = getattr(view, "sortable_columns", [])
        date_filters = getattr(view, "date_filters", [])

        # ── Fields that become dropdowns ──
        for field in exact_filters:
            try:
                model_field = queryset.model._meta.get_field(field)
            except Exception:
                continue

            # Skip fields without choices
            if not getattr(model_field, "choices", None):
                continue

            allowed_values = getattr(view, f"allowed_{field}_values", None)
            all_choices = dict(model_field.choices)

            if allowed_values:
                choices = [
                    (value, all_choices[value])
                    for value in allowed_values
                    if value in all_choices
                ]
            else:
                choices = model_field.choices

            select_attrs = {"class": SELECT_CLASSES}
            select_attrs["onchange"] = "this.form.submit()"

            dynamic_filters[field] = django_filters.ChoiceFilter(
                field_name=field,
                lookup_expr="exact",
                label=field.replace("_", " ").title(),
                choices=choices,
                widget=forms.Select(attrs=select_attrs),
                required=False,
            )

        # ── GT / LT / Ordering ── (unchanged)
        for f in gt_filters:
            dynamic_filters[f"{f}_gt"] = django_filters.NumberFilter(
                field_name=f,
                lookup_expr="gt",
                label=f"{f.replace('_', ' ')} >",
                widget=forms.NumberInput(
                    attrs={
                        "placeholder": "Greater than...",
                        "class": DEFAULT_FILTER_CLASSES,
                    }
                ),
            )

        for f in lt_filters:
            dynamic_filters[f"{f}_lt"] = django_filters.NumberFilter(
                field_name=f,
                lookup_expr="lt",
                label=f"{f.replace('_', ' ')} <",
                widget=forms.NumberInput(
                    attrs={
                        "placeholder": "Less than...",
                        "class": DEFAULT_FILTER_CLASSES,
                    }
                ),
            )

        if sortable_fields:
            dynamic_filters["ordering"] = django_filters.OrderingFilter(
                fields=[(f, f) for f in sortable_fields]
            )

        for field in date_filters:
            dynamic_filters[f"{field}_from"] = django_filters.DateFilter(
                field_name=field,
                lookup_expr="gte",
                label="From",
                widget=forms.DateInput(
                    attrs={
                        "type": "date",
                        "class": DEFAULT_FILTER_CLASSES,
                    }
                ),
            )

            dynamic_filters[f"{field}_to"] = django_filters.DateFilter(
                field_name=field,
                lookup_expr="lte",
                label="To",
                widget=forms.DateInput(
                    attrs={
                        "type": "date",
                        "class": DEFAULT_FILTER_CLASSES,
                    }
                ),
            )

        self.base_filters = {**self.base_filters, **dynamic_filters}

        super().__init__(data=data, queryset=queryset, **kwargs)

        self.form.fields.pop("ordering", None)
        self.search_fields = getattr(view, "search_fields", [])

    def search_filter(self, qs, name, value):

        if not value:
            return qs

        q = Q()

        for field in self.search_fields:
            q |= Q(**{f"{field}__icontains": value})

        return qs.filter(q).distinct()


class ImpactFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        method="search_filter",
        label="Search",
    )

    class Meta:
        model = Publication
        fields = []

    def search_filter(self, queryset, name, value):
        if not value:
            return queryset

        return queryset.filter(
            Q(journal__name__icontains=value)
            | Q(title__icontains=value)
            | Q(doi__icontains=value)
        )


class PublicationFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(
        field_name="date_published", lookup_expr="gte", label="From"
    )
    date_to = django_filters.DateFilter(
        field_name="date_published", lookup_expr="lte", label="To"
    )

    document_type = django_filters.MultipleChoiceFilter(
        choices=Publication.DOC_TYPE_CHOICES, label="Document Type"
    )

    department = django_filters.ModelMultipleChoiceFilter(
        queryset=Department.objects.all(), label="Department"
    )

    rri_role = django_filters.MultipleChoiceFilter(
        field_name="authors__rri_role",
        choices=[
            ("Faculty", "Faculty"),
            ("Student", "Student"),
            ("External", "External"),
        ],
        label="RRI Role",
    )

    year = django_filters.NumberFilter(
        field_name="date_published__year", label="Publication Year"
    )

    class Meta:
        model = Publication
        fields = []
