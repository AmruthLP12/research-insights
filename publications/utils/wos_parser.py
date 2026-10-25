"""
Web of Science (WoS) TSV export parser.

Parses tab-delimited full-record exports from Web of Science into structured
dictionaries for publication and author review.
"""

import csv
import logging
import re
import sys

logger = logging.getLogger(__name__)

# Support large fields (such as comprehensive author affiliation lists and abstracts)
try:
    csv.field_size_limit(sys.maxsize)
except OverflowError:
    csv.field_size_limit(2147483647)

# Core Web of Science two-letter field tags to validate standard export format
WOS_CORE_TAGS = frozenset({
    "SO", "AF", "AU", "DT", "PY", "DI", "UT", "PT", "C1", "VL", "IS", "BP", "EP", "AR", "ARTN"
})


def split_name(full_name: str) -> tuple[str, str]:
    """Split an author's name formatted as 'Last, First' into first and last name."""
    if not full_name:
        return "", ""
    parts = full_name.split(",")
    last = parts[0].strip()
    first = parts[1].strip() if len(parts) > 1 else ""
    return first, last


def extract_country(address: str) -> str:
    """Extract the country name from the trailing segment of an address string."""
    if not address:
        return ""
    parts = address.split(",")
    return parts[-1].strip()


def parse_affiliation_blocks(c1_field: str | None) -> dict[str, list[dict]]:
    """
    Parses Web of Science C1 author affiliation blocks.

    Format: [Author A; Author B] Affiliation text [Author C] Other affiliation
    Returns:
    {
      "Author A": [ {aff}, ... ],
      "Author B": [ {aff}, ... ]
    }
    """
    mapping = {}
    if not c1_field:
        return mapping

    blocks = re.findall(r"\[(.*?)\]\s*([^[]+)", c1_field)

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


def parse_wos_file(file_obj) -> list[dict]:
    """
    Parse an uploaded Web of Science tab-delimited export file.

    Handles UTF-8 and UTF-8 with BOM (utf-8-sig) encodings. Validates that the
    file contains standard Web of Science headers (including mandatory 'TI').

    Returns a list of publication record dictionaries, or an empty list if the
    file is invalid, empty, or contains no valid publication rows.
    """
    try:
        raw = file_obj.read()
    except Exception as exc:
        logger.warning("Failed to read uploaded file: %s", exc)
        return []

    if isinstance(raw, str):
        text = raw
    elif isinstance(raw, (bytes, bytearray)):
        try:
            # utf-8-sig automatically strips UTF-8 BOM (\xef\xbb\xbf)
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", errors="replace")
    else:
        return []

    lines = text.splitlines()
    if not lines:
        return []

    try:
        reader = csv.DictReader(lines, delimiter="\t")
    except Exception as exc:
        logger.warning("Failed to initialize TSV DictReader: %s", exc)
        return []

    raw_fieldnames = reader.fieldnames
    if not raw_fieldnames:
        return []

    # Clean fieldnames (strip whitespace/BOM remnants)
    fieldnames = {f.strip() for f in raw_fieldnames if f}

    # Validate that mandatory Title field and at least one other standard WoS tag exist
    if "TI" not in fieldnames or not (fieldnames & WOS_CORE_TAGS):
        logger.info("Uploaded file lacks standard Web of Science headers ('TI' and core tags).")
        return []

    records = []

    try:
        for row in reader:
            if not row:
                continue

            raw_title = row.get("TI")
            if not raw_title or not str(raw_title).strip():
                # Skip empty lines, summary rows, or EOF tags (e.g., 'EF')
                continue

            title = str(raw_title).strip()

            # -----------------------
            # PAGE NUMBER OR ARTICLE NUMBER
            # -----------------------
            page_number = ""
            bp = (row.get("BP") or "").strip()
            ep = (row.get("EP") or "").strip()
            ar = (row.get("AR") or "").strip()
            artn = (row.get("ARTN") or "").strip()

            if bp and ep:
                page_number = f"{bp}-{ep}"
            elif ar:
                page_number = ar
            elif artn:
                page_number = artn

            article_number = ar or artn

            # -----------------------
            # Publication
            # -----------------------
            py = (row.get("PY") or "").strip()
            date_published = f"{py}-01-01" if py else None

            publication = {
                "title": title,
                "journal_name": (row.get("SO") or "").strip() or row.get("SO"),
                "document_type": (row.get("DT") or "").strip() or row.get("DT"),
                "date_published": date_published,
                "volume": (row.get("VL") or "").strip() or row.get("VL"),
                "issue": (row.get("IS") or "").strip() or row.get("IS"),
                "page_number": page_number,
                "article_number": article_number,
                "doi": (row.get("DI") or "").strip() or row.get("DI"),
            }

            # -----------------------
            # Authors
            # -----------------------
            af_raw = row.get("AF") or row.get("AU") or ""
            author_names = [
                a.strip()
                for a in af_raw.split(";")
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
    except csv.Error as exc:
        logger.warning("Encountered CSV parsing error while reading rows: %s", exc)

    return records
