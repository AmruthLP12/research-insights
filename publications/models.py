# publications/models.py
from django.db import models
from django.conf import settings
from django.urls import reverse


# --------------------------
# Department
# --------------------------
class Department(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


# --------------------------
# Journal
# --------------------------
class Journal(models.Model):
    name = models.CharField(max_length=255, unique=True)
    publisher = models.CharField(max_length=255, blank=True, null=True)
    impact_factor = models.FloatField(blank=True, null=True)
    last_updated = models.DateField(auto_now=True)

    def __str__(self):
        return self.name


# --------------------------
# Author
# --------------------------
class Author(models.Model):
    RRI_ROLE_CHOICES = [
        ('Faculty', 'Faculty'),
        ('Retired Faculty', 'Retired Faculty'),
        ('Adjunct Faculty', 'Adjunct Faculty'),
        ('Research Scholar', 'Research Scholar'),
        ('Post Doctoral Fellow (PDF)', 'Post Doctoral Fellow (PDF)'),
        ('Research Assistant/Associate (RA)', 'Research Assistant/Associate (RA)'),
        ('Staff', 'Staff'),
        ('External', 'External'),
    ]

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    rri_role = models.CharField(
        max_length=100,
        choices=RRI_ROLE_CHOICES,
        blank=True,
        null=True
    )

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# --------------------------
# Affiliation
# --------------------------
class Affiliation(models.Model):
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = "Affiliation"
        verbose_name_plural = "Affiliations"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.country})" if self.country else self.name


# --------------------------
# AuthorAffiliation
# --------------------------
class AuthorAffiliation(models.Model):
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name="author_affiliations"
    )
    affiliation = models.ForeignKey(
        Affiliation,
        on_delete=models.CASCADE,
        related_name="author_affiliations"
    )
    publication = models.ForeignKey(
        'Publication',
        on_delete=models.CASCADE,
        related_name='author_affiliations',
        blank=True,
        null=True
    )
    is_primary = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Author Affiliation"
        verbose_name_plural = "Author Affiliations"

    def __str__(self):
        return f"{self.author} — {self.affiliation}"


# --------------------------
# Publication
# --------------------------
class Publication(models.Model):
    DOC_TYPE_CHOICES = [
        ('Journal Article', 'Journal Article'),
        ('Miscellaneous Article', 'Miscellaneous Article'),
        ('Conference Paper', 'Conference Paper'),
        ('Book/Book Chapter', 'Book/Book Chapter'),
        ('Editorial', 'Editorial'),
        ('Letter', 'Letter'),
        ('Patent', 'Patent'),
        ('Book Review', 'Book Review'),
    ]

    COLLAB_TYPE_CHOICES = [
        ('National', 'National'),
        ('International', 'International'),
        ('National/International', 'National/International'),
        ('Departmental', 'Departmental'),
    ]

    document_type = models.CharField(max_length=50, choices=DOC_TYPE_CHOICES)
    date_published = models.DateField()
    title = models.CharField(max_length=500)

    journal = models.ForeignKey(
        Journal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    volume = models.CharField(max_length=50, blank=True, null=True)
    issue = models.CharField(max_length=50, blank=True, null=True)
    page_number = models.CharField(max_length=50, blank=True, null=True)
    doi = models.CharField(max_length=255, blank=True, null=True)

    collaboration_type = models.CharField(
        max_length=50,
        choices=COLLAB_TYPE_CHOICES
    )

    departments = models.ManyToManyField(
        Department,
        related_name="publications",
        blank=True
    )

    authors = models.ManyToManyField(
        Author,
        related_name="publications",
        blank=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_published"]

    def __str__(self):
        return self.title

    # ✅ REQUIRED for dashboard + django-tables2
    def get_absolute_url(self):
        return reverse("publications:publication_detail", args=[self.id])


# --------------------------
# Year-wise citations
# --------------------------
class Citation(models.Model):
    YEAR_CHOICES = [(y, y) for y in range(1900, 2051)]

    publication = models.ForeignKey(
        Publication,
        on_delete=models.CASCADE,
        related_name="yearly_citations"
    )
    year = models.IntegerField(choices=YEAR_CHOICES)
    wos_citations = models.PositiveIntegerField(default=0)
    gs_citations = models.PositiveIntegerField(default=0)
    scopus_citations = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("publication", "year")
        ordering = ['year']

    def __str__(self):
        return f"{self.publication.title} – {self.year}"
