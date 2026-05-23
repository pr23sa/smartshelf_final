import re
import sqlite3
from pathlib import Path

from pypdf import PdfReader


SCRIPT_DIR = Path(__file__).resolve().parent
DB_PATH = SCRIPT_DIR / "library.db"


def clean_title(value):
    if not value:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def is_valid_title(value):
    title = clean_title(value)
    return bool(title and re.search(r"[A-Za-z]", title))


def find_books_table(conn):
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
    ).fetchall()
    print("Tables in sqlite_master:")
    if not tables:
        print("  (none)")
        return None

    for row in tables:
        print(f"  {row['name']}")

    for row in tables:
        table = row["name"]
        columns = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
        names = {col["name"] for col in columns}
        if {"title", "pdf_path"}.issubset(names):
            return table
    return None


def resolve_pdf_path(pdf_path):
    raw_path = Path(pdf_path)
    candidates = []
    if raw_path.is_absolute():
        candidates.append(raw_path)
    else:
        candidates.append(SCRIPT_DIR / raw_path)
        candidates.append(SCRIPT_DIR / "uploads" / "pdfs" / raw_path)

    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0] if candidates else raw_path


def extract_pdf_title(pdf_path):
    reader = PdfReader(str(pdf_path))

    metadata_title = ""
    if reader.metadata:
        metadata_title = clean_title(reader.metadata.title)
    if metadata_title:
        return metadata_title

    if not reader.pages:
        return ""

    text = reader.pages[0].extract_text() or ""
    for line in text.splitlines():
        title = clean_title(line)
        if title:
            return title
    return ""


def main():
    print(f"Database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    table = find_books_table(conn)
    if not table:
        conn.close()
        print("No books table with title and pdf_path columns found.")
        print("DONE - 0 books updated")
        return

    print(f"Using books table: {table}")
    columns = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    column_names = {col["name"] for col in columns}
    id_column = "id" if "id" in column_names else "rowid"

    rows = conn.execute(
        f'SELECT {id_column} AS book_id, title, pdf_path FROM "{table}" '
        "WHERE pdf_path IS NOT NULL AND TRIM(pdf_path) != ''"
    ).fetchall()
    print(f"Books with pdf_path: {len(rows)}")

    updated = 0
    for row in rows:
        old_title = row["title"]
        pdf_path = resolve_pdf_path(row["pdf_path"])

        try:
            extracted_title = extract_pdf_title(pdf_path)
        except Exception as exc:
            extracted_title = ""
            print(f"ERROR opening PDF for book {row['book_id']}: {pdf_path}")
            print(f"  {type(exc).__name__}: {exc}")

        print(f"Old DB title: {old_title}")
        print(f"Extracted PDF title: {extracted_title}")

        if is_valid_title(extracted_title):
            conn.execute(
                f'UPDATE "{table}" SET title = ? WHERE {id_column} = ?',
                (clean_title(extracted_title), row["book_id"]),
            )
            updated += 1
            print("Updated: yes")
        else:
            print("Updated: no")
        print()

    conn.commit()
    conn.close()
    print(f"DONE - {updated} books updated")


if __name__ == "__main__":
    main()
