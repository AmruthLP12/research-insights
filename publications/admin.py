from django.contrib import admin
from .models import (
    Publication,
    Author,
    Journal,
    Department,
    Affiliation,
    AuthorAffiliation,
    Citation
)

# =========================================================
# Inline: AuthorAffiliation
# =========================================================
class AuthorAffiliationInline(admin.TabularInline):
    model = AuthorAffiliation
    extra = 0
    autocomplete_fields = ("author", "affiliation")
    verbose_name = "Author Affiliation"
    verbose_name_plural = "Author Affiliations"


# =========================================================
# Author Admin
# =========================================================
@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "rri_role")
    list_filter = ("rri_role",)
    search_fields = ("first_name", "last_name")
    inlines = (AuthorAffiliationInline,)


# =========================================================
# Department Admin
# =========================================================
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


# =========================================================
# Journal Admin
# =========================================================
@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ("name", "publisher", "impact_factor", "last_updated")
    search_fields = ("name", "publisher")
    ordering = ("name",)


# =========================================================
# Publication Admin
# =========================================================
@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "journal",
        "date_published",
        "collaboration_type",
        "created_by",
    )

    list_filter = (
        "collaboration_type",
        "date_published",
        "departments",
        "journal",
    )

    search_fields = (
        "title",
        "doi",
        "journal__name",
        "authors__first_name",
        "authors__last_name",
    )

    autocomplete_fields = ("journal", "authors", "departments")
    filter_horizontal = ()  # replaced by autocomplete_fields

    readonly_fields = ("created_by",)

    fieldsets = (
        ("Publication Metadata", {
            "fields": (
                "title",
                "document_type",
                "date_published",
                "journal",
                ("volume", "issue", "page_number"),
                "doi",
            )
        }),
        ("Collaboration & Departments", {
            "fields": ("collaboration_type", "departments")
        }),
        ("Authors", {
            "fields": ("authors",)
        }),
        ("Administrative", {
            "fields": ("created_by",)
        }),
    )

    def save_model(self, request, obj, form, change):
        """
        Automatically set created_by on first save.
        """
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# =========================================================
# Affiliation Admin
# =========================================================
@admin.register(Affiliation)
class AffiliationAdmin(admin.ModelAdmin):
    list_display = ("name", "country")
    list_filter = ("country",)
    search_fields = ("name", "country")
    ordering = ("name",)


# =========================================================
# Citation Admin
# =========================================================
@admin.register(Citation)
class CitationAdmin(admin.ModelAdmin):
    list_display = (
        "publication",
        "year",
        "wos_citations",
        "gs_citations",
        "scopus_citations",
    )
    list_filter = ("year", "publication")
    search_fields = ("publication__title",)
