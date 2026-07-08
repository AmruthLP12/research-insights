import django_tables2 as tables
from publications.models import Publication

class PublicationTable(tables.Table):
    title = tables.Column(linkify=True)

    class Meta:
        model = Publication
        template_name = "django_tables2/bootstrap.html"
        fields = (
            "title",
            "document_type",
            "journal",
            "date_published",
            "doi",
        )
