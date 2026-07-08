# publications/forms.py

from django import forms
from .models import Publication, Author, Department

# Tailwind utility classes
TAILWIND_INPUT = (
    "block w-full border border-gray-300 rounded-md px-3 py-2 "
    "focus:outline-none focus:ring-2 focus:ring-[#0A4DA3]"
)
TAILWIND_SELECT = (
    "block w-full border border-gray-300 rounded-md px-3 py-2 bg-white "
    "focus:outline-none focus:ring-2 focus:ring-[#0A4DA3]"
)


# =====================================================
# Publication Form
# =====================================================
class PublicationForm(forms.ModelForm):
    departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.all(),
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                "class": TAILWIND_SELECT,
                "size": 5,
            }
        ),
    )

    class Meta:
        model = Publication
        fields = [
            "document_type",
            "departments",
            "date_published",
            "title",
            "journal",
            "volume",
            "issue",
            "page_number",
            "doi",
            "collaboration_type",
        ]
        widgets = {
            "document_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "date_published": forms.DateInput(
                attrs={"type": "date", "class": TAILWIND_INPUT}
            ),
            "title": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "journal": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "volume": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "issue": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "page_number": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "doi": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "collaboration_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
        }


# =====================================================
# Author Form (USED BY WoS REVIEW)
# =====================================================
class AuthorForm(forms.ModelForm):
    affiliations_json = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
    )

    class Meta:
        model = Author
        fields = [
            "first_name",
            "last_name",
            "rri_role",
            "affiliations_json",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "last_name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "rri_role": forms.Select(attrs={"class": TAILWIND_SELECT}),
        }
