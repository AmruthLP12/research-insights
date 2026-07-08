import csv
import re


def split_name(full_name):
    parts = full_name.split(",")
    last = parts[0].strip()
    first = parts[1].strip() if len(parts) > 1 else ""
    return first, last


def extract_country(address):
    if not address:
        return ""
    parts = address.split(",")
    return parts[-1].strip()


def parse_affiliation_blocks(c1_field):
    """
    Parses:
    [Author A; Author B] Affiliation text
    Returns:
    {
      "Author A": [ {aff}, {aff} ],
      "Author B": [ {aff} ]
    }
    """
    mapping = {}

    blocks = re.findall(r"\[(.*?)\]\s*([^[]+)", c1_field or "")

    for authors_part, affiliation_text in blocks:
        authors = [a.strip() for a in authors_part.split(";")]
        country = extract_country(affiliation_text)

        aff = {
            "name": affiliation_text.strip(),
            "country": country,
            "is_primary": True,
        }

        for author in authors:
            mapping.setdefault(author, []).append(aff)

    return mapping


def parse_wos_file(file_obj):
    decoded = file_obj.read().decode("utf-8", errors="ignore").splitlines()
    reader = csv.DictReader(decoded, delimiter="\t")

    records = []

    for row in reader:

        # -----------------------
        # PAGE NUMBER OR ARTICLE NUMBER
        # -----------------------
        page_number = ""

        if row.get("BP") and row.get("EP"):
            page_number = f"{row.get('BP')}-{row.get('EP')}"
        elif row.get("AR"):
            page_number = row.get("AR")
        elif row.get("ARTN"):
            page_number = row.get("ARTN")

        # -----------------------
        # Publication
        # -----------------------
        publication = {
            "title": row.get("TI"),
            "journal_name": row.get("SO"),
            "document_type": row.get("DT"),
            "date_published": f"{row.get('PY')}-01-01" if row.get("PY") else None,
            "volume": row.get("VL"),
            "issue": row.get("IS"),
            "page_number": page_number,
            "doi": row.get("DI"),
        }

        # -----------------------
        # Authors
        # -----------------------
        author_names = [
            a.strip()
            for a in (row.get("AF") or "").split(";")
            if a.strip()
        ]

        affiliation_map = parse_affiliation_blocks(row.get("C1"))

        authors = []

        for full_name in author_names:
            first, last = split_name(full_name)

            authors.append({
                "first_name": first,
                "last_name": last,
                "affiliations_json": affiliation_map.get(full_name, []),
            })

        records.append({
            "publication": publication,
            "authors": authors,
        })

    return records
