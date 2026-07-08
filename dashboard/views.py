from django.shortcuts import render
from django.db.models import Count, Avg, Sum, Max
from dashboard.filters import DynamicFilter
from publications.models import (
    Publication,
    Author,
    AuthorAffiliation,
)
from django.views.generic import TemplateView
from django.core.paginator import Paginator


class DashboardHomeView(TemplateView):
    template_name = "dashboard/dashboard.html"

    # -----------------------
    # DynamicFilter settings
    # -----------------------

    search_fields = [
        "title",
        "journal__name",
        "doi",
    ]

    gt_filters = []

    lt_filters = []

    exact_filters = [
        "document_type",
        "collaboration_type",
    ]

    sortable_columns = [
        "date_published",
    ]

    date_filters = [
        "date_published",
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        queryset = Publication.objects.select_related("journal").prefetch_related(
            "authors"
        )

        filterset = DynamicFilter(
            self.request.GET,
            queryset=queryset,
            view=self,
        )

        publications = filterset.qs

        summary = publications.aggregate(
            total_publications=Count("id"),
            total_impact_factor=Sum("journal__impact_factor"),
            avg_impact_factor=Avg("journal__impact_factor"),
        )

        recent_publications = publications.annotate(
            author_count=Count("authors", distinct=True)
        ).order_by("-date_published")[:5]

        document_counts = list(
            publications.values("document_type")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        year_stats = list(
            publications.values("date_published__year")
            .annotate(total=Count("id"))
            .order_by("date_published__year")
        )

        context.update(
            {
                "filter": filterset,
                # KPI
                "total_publications": summary["total_publications"] or 0,
                "total_impact_factor": summary["total_impact_factor"] or 0,
                "avg_impact_factor": summary["avg_impact_factor"] or 0,
                "active_authors": (
                    Author.objects.filter(publications__in=publications)
                    .distinct()
                    .count()
                ),
                # Charts
                "document_counts": document_counts,
                "year_stats": year_stats,
                # Table
                "recent_publications": recent_publications,
            }
        )

        return context


# =====================================================
# DOCUMENT TYPES
# =====================================================
class DocumentTypesView(TemplateView):
    template_name = "dashboard/document_types.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        document_types = (
            Publication.objects.values("document_type")
            .annotate(
                total_publications=Count("id", distinct=True),
                average_impact_factor=Avg("journal__impact_factor"),
                total_impact_factor=Sum("journal__impact_factor"),
            )
            .order_by("-total_publications")
        )

        document_types_data = list(document_types)

        summary = Publication.objects.aggregate(
            total_publications=Count("id"),
            total_impact_factor=Sum("journal__impact_factor"),
            average_impact_factor=Avg("journal__impact_factor"),
            highest_impact_factor=Max("journal__impact_factor"),
        )

        context.update(
            {
                # Table
                "document_types": document_types,
                "document_types_data": document_types_data,
                # KPI Cards
                "document_type_count": len(document_types_data),
                "document_total_publications": summary["total_publications"] or 0,
                "document_total_impact": summary["total_impact_factor"] or 0,
                "document_average_impact": summary["average_impact_factor"] or 0,
                "document_highest_impact": summary["highest_impact_factor"] or 0,
            }
        )

        return context


# =====================================================
# AUTHORS
# =====================================================
def authors_view(request):
    table = (
        Publication.objects.values(
            "authors__id",
            "authors__first_name",
            "authors__last_name",
            "authors__rri_role",
            "authors__author_affiliations__affiliation__name",
        )
        .annotate(
            total=Count("id", distinct=True),
            avg_impact_factor=Avg("journal__impact_factor"),
            total_impact_factor=Sum("journal__impact_factor"),
        )
        .order_by("-total")
    )

    return render(request, "dashboard/authors.html", {"table": table})


# =====================================================
# JOURNALS
# =====================================================
def journals_view(request):
    table = (
        Publication.objects.values(
            "journal__name",
            "journal__impact_factor",
        )
        .annotate(
            total=Count("id", distinct=True),
            avg_if=Avg("journal__impact_factor"),
            total_impact_factor=Sum("journal__impact_factor"),
        )
        .order_by("-total")
    )

    return render(request, "dashboard/journals.html", {"journals": table})


# =====================================================
# DEPARTMENTS
# =====================================================
def departments_view(request):
    table = (
        Publication.objects.values("departments__name")
        .annotate(
            total=Count("id", distinct=True),
            dept_avg_if=Avg("journal__impact_factor"),
            dept_total_impact_factor=Sum("journal__impact_factor"),
        )
        .order_by("-total")
    )
    return render(request, "dashboard/departments.html", {"table": table})


# =====================================================
# COLLABORATION OVERVIEW
# =====================================================
class CollaborationView(TemplateView):
    template_name = "dashboard/collaboration.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        collaboration_types = (
            Publication.objects.values("collaboration_type")
            .annotate(
                total_publications=Count("id", distinct=True),
                average_impact_factor=Avg("journal__impact_factor"),
                total_impact_factor=Sum("journal__impact_factor"),
            )
            .order_by("-total_publications")
        )

        collaboration_types_data = list(collaboration_types)

        summary = Publication.objects.aggregate(
            total_publications=Count("id"),
            total_impact_factor=Sum("journal__impact_factor"),
            average_impact_factor=Avg("journal__impact_factor"),
            highest_impact_factor=Max("journal__impact_factor"),
        )

        context["collaboration_summary"] = list(
            Publication.objects.values("collaboration_type")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        context["collaboration_chart_data"] = context["collaboration_summary"]

        context["collaboration_total_publications"] = Publication.objects.count()

        if context["collaboration_summary"]:
            context["collaboration_top_type"] = context["collaboration_summary"][0][
                "collaboration_type"
            ]
            context["collaboration_top_count"] = context["collaboration_summary"][0][
                "total"
            ]
        else:
            context["collaboration_top_type"] = None
            context["collaboration_top_count"] = 0

        context.update(
            {
                # Table
                "collaboration_types": collaboration_types,
                "collaboration_types_data": collaboration_types_data,
                # KPI Cards
                "collaboration_type_count": len(collaboration_types_data),
                "collaboration_total_publications": summary["total_publications"] or 0,
                "collaboration_total_impact": summary["total_impact_factor"] or 0,
                "collaboration_average_impact": summary["average_impact_factor"] or 0,
                "collaboration_highest_impact": summary["highest_impact_factor"] or 0,
            }
        )

        return context


# =====================================================
# COUNTRY COLLABORATION
# =====================================================
def country_collaboration_view(request):
    table = (
        AuthorAffiliation.objects.values("country")
        .annotate(publications=Count("publication", distinct=True))
        .order_by("-publications")
    )

    return render(
        request,
        "dashboard/collaboration.html",
        {
            "table": table,
            "title": "Country-wise Collaboration",
        },
    )


# =====================================================
# INSTITUTION COLLABORATION
# =====================================================
def institution_collaboration_view(request):
    table = (
        AuthorAffiliation.objects.values("institution")
        .annotate(publications=Count("publication", distinct=True))
        .order_by("-publications")
    )

    return render(
        request,
        "dashboard/collaboration.html",
        {
            "table": table,
            "title": "Institution-wise Collaboration",
        },
    )


# =====================================================
# PUBLICATION TRENDS
# =====================================================
class TrendsView(TemplateView):
    template_name = "dashboard/trends.html"

    search_fields = [
        "title",
        "journal__name",
        "doi",
    ]

    exact_filters = [
        "document_type",
        "collaboration_type",
    ]

    date_filters = [
        "date_published",
    ]

    sortable_columns = [
        "date_published",
    ]

    gt_filters = []
    lt_filters = []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        queryset = Publication.objects.select_related("journal")

        filterset = DynamicFilter(
            self.request.GET,
            queryset=queryset,
            view=self,
        )

        filtered = filterset.qs

        publication_trends = (
            filtered.values("date_published__year")
            .annotate(
                total=Count("id"),
                avg_if=Avg("journal__impact_factor"),
                total_impact_factor=Sum("journal__impact_factor"),
            )
            .order_by("date_published__year")
        )

        publication_trends_data = list(publication_trends)

        paginator = Paginator(publication_trends, 10)

        page_number = self.request.GET.get("page")

        page_obj = paginator.get_page(page_number)

        totals = filtered.aggregate(
            total_publications=Count("id"),
            total_impact=Sum("journal__impact_factor"),
        )

        latest_year = (
            publication_trends_data[-1]["date_published__year"]
            if publication_trends_data
            else None
        )

        yoy_change = None

        if len(publication_trends_data) >= 2:
            previous = publication_trends_data[-2]["total"]
            current = publication_trends_data[-1]["total"]

            if previous:
                yoy_change = ((current - previous) / previous) * 100

        context.update(
            {
                "filter": filterset,
                "page_obj": page_obj,
                "publication_trends": page_obj,
                "publication_trends_data": publication_trends_data,
                "trend_years_tracked": len(publication_trends_data),
                "trend_total_publications": totals["total_publications"] or 0,
                "trend_total_impact": totals["total_impact"] or 0,
                "trend_latest_year": latest_year,
                "trend_yoy_change": yoy_change,
            }
        )

        return context


# =====================================================
# IMPACT ANALYSIS
# =====================================================
class ImpactView(TemplateView):
    template_name = "dashboard/impact.html"

    # Used by DynamicFilter
    search_fields = [
        "journal__name",
        "title",
        "doi",
    ]

    sortable_columns = [
        "date_published",
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        queryset = Publication.objects.select_related("journal")

        filterset = DynamicFilter(
            self.request.GET,
            queryset=queryset,
            view=self,
        )

        filtered = filterset.qs

        journal_impact = (
            filtered.values("journal__name")
            .annotate(
                total_publications=Count("id"),
                average_impact_factor=Avg("journal__impact_factor"),
                total_impact_factor=Sum("journal__impact_factor"),
            )
            .order_by("-average_impact_factor")
        )

        journal_impact_data = list(journal_impact)

        paginator = Paginator(journal_impact_data, 10)

        page_obj = paginator.get_page(self.request.GET.get("page"))

        summary = filtered.aggregate(
            total_publications=Count("id"),
            total_impact_factor=Sum("journal__impact_factor"),
            average_impact_factor=Avg("journal__impact_factor"),
            highest_impact_factor=Max("journal__impact_factor"),
        )

        context.update(
            {
                "filter": filterset,
                "page_obj": page_obj,
                # Full data (for charts)
                "journal_impact_data": journal_impact_data,
                # KPIs
                "impact_total_journals": len(journal_impact_data),
                "impact_total_publications": summary["total_publications"] or 0,
                "impact_total_factor": summary["total_impact_factor"] or 0,
                "impact_average_factor": summary["average_impact_factor"] or 0,
                "impact_highest_factor": summary["highest_impact_factor"] or 0,
            }
        )

        return context


# =====================================================
# COLLABORATION TYPES
# =====================================================
class CollaborationTypesView(TemplateView):
    template_name = "dashboard/collaboration_types.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        collaboration_types = list(
            Publication.objects.values("collaboration_type")
            .annotate(
                total=Count("id", distinct=True),
                avg_impact_factor=Avg("journal__impact_factor"),
                total_impact_factor=Sum("journal__impact_factor"),
            )
            .order_by("-total")
        )

        context["collaboration_types"] = collaboration_types

        context["collaboration_types_count"] = len(collaboration_types)

        context["collaboration_total_publications"] = sum(
            row["total"] for row in collaboration_types
        )

        context["collaboration_total_impact"] = sum(
            row["total_impact_factor"] or 0 for row in collaboration_types
        )

        context["collaboration_average_impact"] = (
            context["collaboration_total_impact"]
            / context["collaboration_total_publications"]
            if context["collaboration_total_publications"]
            else 0
        )

        return context


# =====================================================
# RRI ROLE
# =====================================================
def rri_role_view(request):
    table = (
        Publication.objects.values("authors__rri_role")
        .annotate(
            total=Count("id", distinct=True),
            avg_if=Avg("journal__impact_factor"),
            total_impact_factor=Sum("journal__impact_factor"),
        )
        .order_by("-total")
    )

    return render(request, "dashboard/rri_role.html", {"table": table})
