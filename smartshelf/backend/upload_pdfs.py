#!/usr/bin/env python3
"""
Bulk-match PDFs from one or more zip archives to books and copy into uploads/pdfs/.
Uses sqlite3 + filesystem only (no API, no login).

Usage:
    python upload_pdfs.py web.zip data.zip ai.zip cyber.zip
    python upload_pdfs.py *.zip
    python upload_pdfs.py books.zip --threshold 0.35
"""

import argparse
import difflib
import re
import shutil
import sqlite3
import sys
import tempfile
import zipfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DB_PATH = SCRIPT_DIR / "smartshelf.db"
PDF_DIR = SCRIPT_DIR / "uploads" / "pdfs"
DEFAULT_THRESHOLD = 0.35


def normalize_name(text: str) -> str:
    text = Path(text).stem
    text = text.lower()
    text = re.sub(r"[_\-\.]+", " ", text)
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def load_books(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT id, title, author, category FROM books ORDER BY id"
    ).fetchall()
    return [dict(r) for r in rows]


def extract_pdfs_from_zip(zip_path: Path, dest: Path) -> list[Path]:
    if not zip_path.is_file():
        raise FileNotFoundError(f"Zip not found: {zip_path}")

    pdfs: list[Path] = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = info.filename.replace("\\", "/")
            if not name.lower().endswith(".pdf"):
                continue
            base = Path(name).name
            if not base or ".." in Path(name).parts:
                continue

            target = dest / base
            if target.exists():
                stem, suffix = target.stem, target.suffix
                n = 2
                while target.exists():
                    target = dest / f"{stem}_{n}{suffix}"
                    n += 1

            with zf.open(info) as src, open(target, "wb") as out:
                out.write(src.read())
            pdfs.append(target)

    return pdfs


def extract_all_pdfs(zip_paths: list[Path], dest: Path) -> list[Path]:
    all_pdfs: list[Path] = []
    for zip_path in zip_paths:
        print(f"Extracting: {zip_path.name}")
        all_pdfs.extend(extract_pdfs_from_zip(zip_path, dest))
    return sorted(all_pdfs, key=lambda p: p.name.lower())


def match_book(
    pdf_path: Path,
    books: list[dict],
    used_ids: set[int],
    threshold: float,
) -> tuple[dict | None, float]:
    pdf_norm = normalize_name(pdf_path.name)
    if not pdf_norm:
        return None, 0.0

    candidates = [b for b in books if b["id"] not in used_ids]
    if not candidates:
        return None, 0.0

    best_book: dict | None = None
    best_score = 0.0
    for book in candidates:
        score = difflib.SequenceMatcher(
            None, pdf_norm, normalize_name(book["title"])
        ).ratio()
        if score > best_score:
            best_score = score
            best_book = book

    if best_book and best_score >= threshold:
        return best_book, best_score
    return None, best_score


def pdf_filename(book_id: int) -> str:
    return f"book_{book_id}.pdf"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Upload PDFs from one or more zip files to SmartShelf (direct DB)."
    )
    parser.add_argument(
        "zip_paths",
        nargs="+",
        type=Path,
        help="One or more zip files containing PDFs",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=f"Fuzzy match threshold 0-1 (default: {DEFAULT_THRESHOLD})",
    )
    args = parser.parse_args()

    for zp in args.zip_paths:
        if not zp.is_file():
            print(f"Zip not found: {zp}", file=sys.stderr)
            return 1

    if not DB_PATH.is_file():
        print(f"Database not found: {DB_PATH}", file=sys.stderr)
        print("Start the backend once: python app.py", file=sys.stderr)
        return 1

    PDF_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    books = load_books(conn)
    if not books:
        print("No books in database.", file=sys.stderr)
        conn.close()
        return 1

    print(f"Database:   {DB_PATH}")
    print(f"PDF dir:    {PDF_DIR}")
    print(f"Books:      {len(books)}")
    print(f"Zip files:  {len(args.zip_paths)}")
    print(f"Threshold:  {args.threshold}\n")

    matched: list[tuple[str, int, str, float]] = []
    skipped: list[tuple[str, float]] = []

    with tempfile.TemporaryDirectory(prefix="smartshelf_zip_") as tmp:
        pdfs = extract_all_pdfs(args.zip_paths, Path(tmp))
        if not pdfs:
            print("No PDF files found in any zip.", file=sys.stderr)
            conn.close()
            return 1

        print(f"\nFound {len(pdfs)} PDF(s) total.\n")
        used_ids: set[int] = set()

        for pdf_path in pdfs:
            book, score = match_book(pdf_path, books, used_ids, args.threshold)
            if not book:
                skipped.append((pdf_path.name, score))
                print(f"  SKIP  {pdf_path.name}  (best {score:.2f})")
                continue

            used_ids.add(book["id"])
            dest_name = pdf_filename(book["id"])
            dest_path = PDF_DIR / dest_name
            shutil.copy2(pdf_path, dest_path)
            conn.execute(
                "UPDATE books SET pdf_path = ? WHERE id = ?",
                (dest_name, book["id"]),
            )
            matched.append((pdf_path.name, book["id"], book["title"], score))
            print(f"  OK    {pdf_path.name}")
            print(f"        -> [{book['id']}] {book['title']}  ({score:.2f})")

        conn.commit()

    conn.close()

    print("\n" + "=" * 56)
    print("SUMMARY")
    print("=" * 56)
    print(f"  PDFs found:       {len(pdfs)}")
    print(f"  Matched/uploaded: {len(matched)}")
    print(f"  Skipped:          {len(skipped)}")

    if matched:
        print("\nMatched books:")
        for pdf_name, book_id, title, score in matched:
            print(f"  - {pdf_name}")
            print(f"      -> [{book_id}] {title}  ({score:.0%})")

    if skipped:
        print("\nSkipped (no match):")
        for pdf_name, score in skipped:
            print(f"  - {pdf_name}  (best {score:.2f})")

    return 0 if not skipped else 0


if __name__ == "__main__":
    sys.exit(main())
