import sqlite3
import sys
from pathlib import Path

from pypdf import PdfReader

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


SCRIPT_DIR = Path(__file__).resolve().parent
DB_CANDIDATES = [SCRIPT_DIR / "library.db", SCRIPT_DIR / "smartshelf.db"]


def find_books_table(conn):
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
    ).fetchall()
    for row in tables:
        table = row["name"]
        columns = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
        names = {col["name"] for col in columns}
        if {"title", "pdf_path"}.issubset(names):
            return table
    return None


def connect_to_database():
    print("Checking database files:")
    for db_path in DB_CANDIDATES:
        print(f"  {db_path} ({db_path.stat().st_size if db_path.exists() else 'missing'} bytes)")
        if not db_path.exists():
            continue

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        table = find_books_table(conn)
        if table:
            return db_path, conn, table
        conn.close()

    return None, None, None


def resolve_pdf_path(pdf_path):
    raw_path = Path(pdf_path)
    if raw_path.is_absolute():
        return raw_path

    candidates = [
        SCRIPT_DIR / raw_path,
        SCRIPT_DIR / "uploads" / "pdfs" / raw_path,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


def clean_snippet(text):
    return " ".join((text or "").split())[:200]


def main():
    db_path, conn, table = connect_to_database()
    if not conn or not table:
        print("No database with a books table containing title and pdf_path was found.")
        return

    print(f"\nUsing database: {db_path}")
    print(f"Using books table: {table}")

    columns = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    column_names = {col["name"] for col in columns}
    id_column = "id" if "id" in column_names else "rowid"

    rows = conn.execute(
        f'SELECT {id_column} AS book_id, title, pdf_path FROM "{table}" '
        "WHERE pdf_path IS NOT NULL AND TRIM(pdf_path) != '' "
        f"ORDER BY {id_column}"
    ).fetchall()

    print(f"Rows with pdf_path: {len(rows)}")

    for row in rows:
        pdf_path = resolve_pdf_path(row["pdf_path"])
        metadata_title = ""
        page_one_text = ""

        try:
            reader = PdfReader(str(pdf_path))
            if reader.metadata and reader.metadata.title:
                metadata_title = str(reader.metadata.title).strip()
            if reader.pages:
                page_one_text = clean_snippet(reader.pages[0].extract_text())
        except Exception as exc:
            metadata_title = f"ERROR: {type(exc).__name__}: {exc}"
            page_one_text = ""

        print("\n" + "=" * 72)
        print(f"Book ID: {row['book_id']}")
        print(f"Current DB title: {row['title']}")
        print(f"pdf_path: {row['pdf_path']}")
        print(f"Resolved PDF file: {pdf_path}")
        print(f"Metadata title: {metadata_title}")
        print(f"Page 1 first 200 chars: {page_one_text}")

    conn.close()


if __name__ == "__main__":
    main()
