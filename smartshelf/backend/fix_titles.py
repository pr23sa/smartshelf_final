import re
import sqlite3
import sys
from pathlib import Path

from pypdf import PdfReader


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


SCRIPT_DIR = Path(__file__).resolve().parent
DB_PATH = SCRIPT_DIR / "smartshelf.db"
PDF_DIR = SCRIPT_DIR / "uploads" / "pdfs"


def clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def has_letters(value):
    return bool(re.search(r"[A-Za-z]", value or ""))


def is_candidate_line(value):
    line = clean_text(value)
    lowered = line.lower()
    if len(line) <= 5:
        return False
    if "http" in lowered or "www" in lowered:
        return False
    if lowered.startswith(("see discussions", "doi", "article in")):
        return False
    if not has_letters(line):
        return False
    return True


def extract_title(pdf_path):
    reader = PdfReader(str(pdf_path))

    metadata_title = ""
    if reader.metadata and reader.metadata.title is not None:
        metadata_title = clean_text(reader.metadata.title)
    if metadata_title:
        return metadata_title

    if not reader.pages:
        return ""

    text = reader.pages[0].extract_text() or ""
    first_200 = text[:200]
    for line in first_200.splitlines():
        if is_candidate_line(line):
            return clean_text(line)

    return ""


def category_for_title(title, current_category):
    lowered = title.lower()
    if (
        "neural" in lowered
        or "deep learning" in lowered
        or "machine learning" in lowered
        or re.search(r"\bai\b", lowered)
    ):
        return "AI/ML"
    if "data analysis" in lowered or "data science" in lowered or "statistics" in lowered:
        return "Data Science"
    if (
        "web" in lowered
        or "html" in lowered
        or "css" in lowered
        or "javascript" in lowered
        or "frontend" in lowered
    ):
        return "Web Development"
    if (
        "security" in lowered
        or "hacking" in lowered
        or "cyber" in lowered
        or "network" in lowered
    ):
        return "Cybersecurity"
    return current_category


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        "SELECT id, title, category, pdf_path FROM books "
        "WHERE pdf_path IS NOT NULL AND TRIM(pdf_path) != '' "
        "ORDER BY id"
    ).fetchall()

    updated = 0
    skipped = 0

    for row in rows:
        pdf_path = PDF_DIR / row["pdf_path"]
        try:
            new_title = extract_title(pdf_path)
        except Exception as exc:
            new_title = ""
            print(f"SKIPPED {row['pdf_path']} — could not extract title ({type(exc).__name__}: {exc})")

        if not new_title:
            skipped += 1
            if pdf_path.exists():
                print(f"SKIPPED {row['pdf_path']} — could not extract title")
            continue

        new_category = category_for_title(new_title, row["category"])
        print(f"ID: {row['id']} | OLD: {row['title']} | NEW: {new_title}")
        conn.execute(
            "UPDATE books SET title = ?, category = ? WHERE id = ?",
            (new_title, new_category, row["id"]),
        )
        updated += 1

    conn.commit()
    conn.close()
    print(f"DONE — {updated} books updated, {skipped} books skipped")


if __name__ == "__main__":
    main()
