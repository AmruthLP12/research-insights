# publications/views.py

import json
from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.forms import modelformset_factory
from django.urls import reverse

from .forms import PublicationForm, AuthorForm
from .models import Author, Journal, Affiliation, AuthorAffiliation, Publication
from .utils.wos_parser import parse_wos_file
from django.views.generic import DetailView
from django.db.models import Count, Avg, Sum, Max

from dashboard.filters import DynamicFilter

from django.views.generic import TemplateView
from django.core.paginator import Paginator


# =====================================================
# RRI DETECTION
# =====================================================
def is_rri_affiliation(name):
    if not name:
        return False
    name = name.lower()
    return any(
        k in name
        for k in [
            "raman",
            "raman res inst",
            "raman research institute",
            "rri",
        ]
    )


# =====================================================
# PUBLICATIONS LIST ( /publications/ )
# =====================================================


class PublicationsListView(TemplateView):
    template_name = "publications/publications_list.html"

    paginate_by = 10

    search_fields = [
        "title",
        "journal__name",
        "doi",
        "authors__first_name",
        "authors__last_name",
        "departments__name",
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
        "title",
    ]

    gt_filters = []

    lt_filters = []

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        # --------------------------------------------------
        # Publications queryset
        # --------------------------------------------------

        publications = (
            Publication.objects.select_related("journal")
            .prefetch_related(
                "authors",
                "departments",
            )
            .order_by("-date_published")
        )

        # --------------------------------------------------
        # Filters
        # --------------------------------------------------

        filterset = DynamicFilter(
            self.request.GET,
            queryset=publications,
            view=self,
        )

        publications = filterset.qs

        # --------------------------------------------------
        # Pagination
        # --------------------------------------------------

        paginator = Paginator(publications, self.paginate_by)

        page_obj = paginator.get_page(self.request.GET.get("page"))

        # --------------------------------------------------
        # Chart Data - Year wise publications
        # --------------------------------------------------

        publication_trend = (
            publications.values("date_published__year")
            .annotate(
                total=Count("id"),
                total_impact_factor=Sum("journal__impact_factor"),
                average_impact_factor=Avg("journal__impact_factor"),
            )
            .order_by("date_published__year")
        )

        publication_trend_data = list(publication_trend)

        # --------------------------------------------------
        # Summary Cards
        # --------------------------------------------------

        summary = publications.aggregate(
            total_publications=Count("id"),
            total_impact_factor=Sum("journal__impact_factor"),
            average_impact_factor=Avg("journal__impact_factor"),
            highest_impact_factor=Max("journal__impact_factor"),
        )

        context.update(
            {
                # Filters
                "filter": filterset,
                # Table
                "page_obj": page_obj,
                "publications": page_obj,
                # Charts
                "publication_trend_data": publication_trend_data,
                # KPI
                "publication_count": (summary["total_publications"] or 0),
                "publication_total_impact": (summary["total_impact_factor"] or 0),
                "publication_average_impact": (summary["average_impact_factor"] or 0),
                "publication_highest_impact": (summary["highest_impact_factor"] or 0),
                "breadcrumbs": [
                    {
                        "label": "Dashboard",
                        "url": reverse("dashboard:home"),
                    },
                    {
                        "label": "Publications",
                    },
                ],
            }
        )

        return context


class PublicationDetailView(DetailView):
    model = Publication
    template_name = "publications/publication_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        publication = self.object

        context.update(
            {
                "authors": publication.authors.all(),
                "departments": publication.departments.all(),
                "affiliations": publication.author_affiliations.select_related(
                    "author",
                    "affiliation",
                ),
                "citations": publication.yearly_citations.all(),
            }
        )

        return context


# =====================================================
# WOS UPLOAD
# =====================================================
@login_required
def wos_upload(request):
    if request.method == "POST" and request.FILES.get("wos_file"):
        records = parse_wos_file(request.FILES["wos_file"])

        if not records:
            messages.error(
                request,
                "File was read successfully but no publication records were detected. "
                "Please ensure the file is exported as FULL RECORD in tab-delimited format.",
            )
            return redirect("publications:wos_upload")

        request.session["wos_records"] = records
        request.session["wos_index"] = 0

        return redirect("publications:wos_review")

    return render(request, "publications/upload.html")


# =====================================================
# WOS REVIEW
# =====================================================
@login_required
def wos_review(request):
    records = request.session.get("wos_records", [])
    index = request.session.get("wos_index", 0)

    if not records or index >= len(records):
        return redirect("publications:wos_upload")

    record = records[index]
    pub = record["publication"]
    authors = record["authors"]

    journal = None
    if pub.get("journal_name"):
        journal, _ = Journal.objects.get_or_create(name=pub["journal_name"])

    date_published = None
    if pub.get("date_published"):
        date_published = datetime.strptime(pub["date_published"], "%Y-%m-%d").date()

    pub_form = PublicationForm(
        initial={
            "document_type": pub.get("document_type"),
            "date_published": date_published,
            "title": pub.get("title"),
            "journal": journal.id if journal else None,
            "volume": pub.get("volume"),
            "issue": pub.get("issue"),
            "page_number": pub.get("page_number"),
            "doi": pub.get("doi"),
            "collaboration_type": pub.get("collaboration_type"),
        }
    )

    AuthorFormSet = modelformset_factory(
        Author, form=AuthorForm, extra=len(authors), can_delete=True
    )

    initial = []
    for a in authors:
        affiliations = a.get("affiliations_json", [])
        has_rri = any(is_rri_affiliation(x.get("name")) for x in affiliations)

        initial.append(
            {
                "first_name": a.get("first_name"),
                "last_name": a.get("last_name"),
                "rri_role": "" if has_rri else "External",
                "affiliations_json": json.dumps(affiliations),
            }
        )

    formset = AuthorFormSet(queryset=Author.objects.none(), initial=initial)

    # Attach decoded affiliations for template display
    for form in formset:
        try:
            form.affiliations_list = json.loads(
                form.initial.get("affiliations_json", "[]")
            )
        except Exception:
            form.affiliations_list = []

    return render(
        request,
        "publications/review.html",
        {
            "pub_form": pub_form,
            "author_formset": formset,
            "index": index + 1,
            "total": len(records),
        },
    )


# =====================================================
# WOS SAVE
# =====================================================
@login_required
@transaction.atomic
def wos_save(request):
    if request.method != "POST":
        return redirect("publications:wos_review")

    records = request.session.get("wos_records", [])
    index = request.session.get("wos_index", 0)

    if not records or index >= len(records):
        return redirect("publications:wos_upload")

    pub_form = PublicationForm(request.POST)

    AuthorFormSet = modelformset_factory(
        Author, form=AuthorForm, extra=0, can_delete=True
    )
    formset = AuthorFormSet(request.POST, queryset=Author.objects.none())

    if not pub_form.is_valid() or not formset.is_valid():
        messages.error(request, "Please correct the errors below.")
        print(pub_form.errors)
        print(formset.errors)
        return redirect("publications:wos_review")

    publication = pub_form.save(commit=False)
    publication.created_by = request.user
    publication.save()
    pub_form.save_m2m()

    for form in formset:
        if form.cleaned_data.get("DELETE"):
            continue

        author = form.save()
        publication.authors.add(author)

        affiliations = json.loads(form.cleaned_data.get("affiliations_json", "[]"))

        for aff in affiliations:
            affiliation, _ = Affiliation.objects.get_or_create(
                name=aff.get("name"),
                country=aff.get("country"),
            )
            AuthorAffiliation.objects.create(
                author=author,
                affiliation=affiliation,
                publication=publication,
            )

    # advance to next record
    request.session["wos_index"] = index + 1

    if request.session["wos_index"] >= len(records):
        request.session.pop("wos_records", None)
        request.session.pop("wos_index", None)
        return redirect("publications:wos_success")

    return redirect("publications:wos_review")


# =====================================================
# SUCCESS
# =====================================================
def wos_success(request):
    return render(request, "publications/wos_success.html")
