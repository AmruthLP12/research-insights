from django.shortcuts import render
from django.db.models import Count, Avg, Sum, Max, Prefetch
from django.urls import reverse
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

    paginate_by = 10

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

        publications = Publication.objects.select_related("journal")

        filterset = DynamicFilter(
            self.request.GET,
            queryset=publications,
            view=self,
        )

        publications = filterset.qs

        document_types = (
            publications.values("document_type")
            .annotate(
                total_publications=Count("id"),
                average_impact_factor=Avg("journal__impact_factor"),
                total_impact_factor=Sum("journal__impact_factor"),
            )
            .order_by("-total_publications")
        )

        paginator = Paginator(document_types, self.paginate_by)
        page_obj = paginator.get_page(self.request.GET.get("page"))

        summary = publications.aggregate(
            total_publications=Count("id"),
            total_impact_factor=Sum("journal__impact_factor"),
            average_impact_factor=Avg("journal__impact_factor"),
            highest_impact_factor=Max("journal__impact_factor"),
        )

        context.update(
            {
                "filter": filterset,
                # Table
                "page_obj": page_obj,
                # Charts
                "document_types_data": list(document_types),
                # KPI Cards
                "document_type_count": page_obj.paginator.count,
                "document_total_publications": summary["total_publications"] or 0,
                "document_total_impact": summary["total_impact_factor"] or 0,
                "document_average_impact": summary["average_impact_factor"] or 0,
                "document_highest_impact": summary["highest_impact_factor"] or 0,
                # Header
                "breadcrumbs": [
                    {
                        "label": "Dashboard",
                        "url": reverse("dashboard:home"),
                    },
                    {
                        "label": "Document Types",
                    },
                ],
            }
        )

        return context


# =====================================================
# AUTHORS
# =====================================================


class AuthorsView(TemplateView):
    template_name = "dashboard/authors.html"

    paginate_by = 10

    # -----------------------------
    # Search
    # -----------------------------
    search_fields = [
        "first_name",
        "last_name",
    ]

    date_filters = [
        "date_published",
    ]

    # -----------------------------
    # Sorting
    # -----------------------------
    sortable_columns = [
        "first_name",
        "last_name",
        "total_publications",
        "average_impact_factor",
        "total_impact_factor",
    ]

    # -----------------------------
    # Range filters
    # -----------------------------
    gt_filters = [
        "total_publications",
        "total_impact_factor",
        "average_impact_factor",
    ]

    lt_filters = [
        "total_publications",
        "total_impact_factor",
        "average_impact_factor",
    ]

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        # --------------------------------------------------
        # Publications
        # --------------------------------------------------

        publications = Publication.objects.select_related("journal").prefetch_related(
            "authors"
        )

        # --------------------------------------------------
        # Authors Query
        # --------------------------------------------------

        authors = (
            Author.objects.filter(publications__in=publications)
            .annotate(
                total_publications=Count(
                    "publications",
                    distinct=True,
                ),
                total_impact_factor=Sum(
                    "publications__journal__impact_factor",
                ),
                average_impact_factor=Avg(
                    "publications__journal__impact_factor",
                ),
            )
            .prefetch_related(
                Prefetch(
                    "author_affiliations",
                    queryset=AuthorAffiliation.objects.select_related("affiliation"),
                )
            )
            .distinct()
        )

        # --------------------------------------------------
        # Merge duplicate authors
        # --------------------------------------------------

        merged_authors = {}

        for author in authors:
            key = (
                author.first_name.strip().lower(),
                author.last_name.strip().lower(),
            )

            if key not in merged_authors:
                author.merged_publications = author.total_publications or 0

                author.merged_impact = author.total_impact_factor or 0

                author.merged_affiliations = set()

                merged_authors[key] = author

            else:
                existing = merged_authors[key]

                existing.merged_publications += author.total_publications or 0

                existing.merged_impact += author.total_impact_factor or 0

            for affiliation in author.author_affiliations.all():
                merged_authors[key].merged_affiliations.add(
                    affiliation.affiliation.name
                )

        authors = list(merged_authors.values())

        # --------------------------------------------------
        # Final calculated values
        # --------------------------------------------------

        for author in authors:
            author.affiliations = list(author.merged_affiliations)

            author.affiliation_count = len(author.affiliations)

            author.total_publications = author.merged_publications

            author.total_impact_factor = author.merged_impact

            author.average_impact_factor = (
                author.merged_impact / author.merged_publications
                if author.merged_publications
                else 0
            )

        # --------------------------------------------------
        # Apply search AFTER merging
        # --------------------------------------------------

        search = self.request.GET.get("search", "").strip().lower()

        if search:
            authors = [
                author
                for author in authors
                if search in author.first_name.lower()
                or search in author.last_name.lower()
            ]

        # Greater than filters

        total_publications_gt = self.request.GET.get("total_publications_gt")

        if total_publications_gt:
            authors = [
                author
                for author in authors
                if author.total_publications > int(total_publications_gt)
            ]

        total_impact_gt = self.request.GET.get("total_impact_factor_gt")

        if total_impact_gt:
            authors = [
                author
                for author in authors
                if author.total_impact_factor > float(total_impact_gt)
            ]

        average_impact_gt = self.request.GET.get("average_impact_factor_gt")

        if average_impact_gt:
            authors = [
                author
                for author in authors
                if author.average_impact_factor > float(average_impact_gt)
            ]

        # Less than filters

        total_publications_lt = self.request.GET.get("total_publications_lt")

        if total_publications_lt:
            authors = [
                author
                for author in authors
                if author.total_publications < int(total_publications_lt)
            ]

        total_impact_lt = self.request.GET.get("total_impact_factor_lt")

        if total_impact_lt:
            authors = [
                author
                for author in authors
                if author.total_impact_factor < float(total_impact_lt)
            ]

        average_impact_lt = self.request.GET.get("average_impact_factor_lt")

        if average_impact_lt:
            authors = [
                author
                for author in authors
                if author.average_impact_factor < float(average_impact_lt)
            ]

        # Ordering

        ordering = self.request.GET.get("ordering")

        if ordering:
            reverse = ordering.startswith("-")

            field = ordering.replace("-", "")

            authors.sort(
                key=lambda x: getattr(x, field, ""),
                reverse=reverse,
            )

        # --------------------------------------------------
        # Pagination
        # --------------------------------------------------

        paginator = Paginator(authors, self.paginate_by)

        page_obj = paginator.get_page(self.request.GET.get("page"))

        # --------------------------------------------------
        # Chart Data
        # Uses merged + filtered data
        # --------------------------------------------------

        authors_data = [
            {
                "authors__first_name": author.first_name,
                "authors__last_name": author.last_name,
                "total_publications": (author.total_publications),
                "total_impact_factor": float(author.total_impact_factor),
            }
            for author in authors[:10]
        ]

        # --------------------------------------------------
        # Summary
        # Based on merged authors
        # --------------------------------------------------

        summary = {
            "total_publications": sum(a.total_publications for a in authors),
            "total_impact_factor": sum(a.total_impact_factor for a in authors),
            "average_impact_factor": (
                sum(a.average_impact_factor for a in authors) / len(authors)
                if authors
                else 0
            ),
            "highest_impact_factor": max(
                (a.total_impact_factor for a in authors),
                default=0,
            ),
        }

        context.update(
            {
                "page_obj": page_obj,
                "author_count": len(authors),
                "authors_data": authors_data,
                "author_total_publications": (summary["total_publications"]),
                "author_total_impact": (summary["total_impact_factor"]),
                "author_average_impact": (summary["average_impact_factor"]),
                "author_highest_impact": (summary["highest_impact_factor"]),
                "breadcrumbs": [
                    {
                        "label": "Dashboard",
                        "url": "/dashboard/",
                    },
                    {
                        "label": "Authors",
                    },
                ],
            }
        )

        return context


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

    paginate_by = 10

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

        publications = Publication.objects.select_related("journal")

        filterset = DynamicFilter(
            self.request.GET,
            queryset=publications,
            view=self,
        )

        publications = filterset.qs

        collaboration_types = (
            publications.values("collaboration_type")
            .annotate(
                total_publications=Count("id"),
                average_impact_factor=Avg("journal__impact_factor"),
                total_impact_factor=Sum("journal__impact_factor"),
            )
            .order_by("-total_publications")
        )

        collaboration_types_data = list(collaboration_types)

        paginator = Paginator(collaboration_types, self.paginate_by)
        page_obj = paginator.get_page(self.request.GET.get("page"))

        summary = publications.aggregate(
            total_publications=Count("id"),
            total_impact_factor=Sum("journal__impact_factor"),
            average_impact_factor=Avg("journal__impact_factor"),
            highest_impact_factor=Max("journal__impact_factor"),
        )

        top_type = collaboration_types_data[0] if collaboration_types_data else None

        context.update(
            {
                # Filter
                "filter": filterset,
                # Table
                "page_obj": page_obj,
                # Charts
                "collaboration_types_data": collaboration_types_data,
                # Optional chart alias
                "collaboration_chart_data": collaboration_types_data,
                # KPI Cards
                "collaboration_type_count": page_obj.paginator.count,
                "collaboration_total_publications": summary["total_publications"] or 0,
                "collaboration_total_impact": summary["total_impact_factor"] or 0,
                "collaboration_average_impact": summary["average_impact_factor"] or 0,
                "collaboration_highest_impact": summary["highest_impact_factor"] or 0,
                # Top Collaboration Type
                "collaboration_top_type": (
                    top_type["collaboration_type"] if top_type else None
                ),
                "collaboration_top_count": (
                    top_type["total_publications"] if top_type else 0
                ),
                # Header
                "breadcrumbs": [
                    {
                        "label": "Dashboard",
                        "url": reverse("dashboard:home"),
                    },
                    {
                        "label": "Collaboration Overview",
                    },
                ],
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
