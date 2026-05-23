import sqlite3
import sys
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


DB_PATH = Path(__file__).resolve().parent / "smartshelf.db"


def main():
    conn = sqlite3.connect(DB_PATH)

    conn.execute("UPDATE books SET title = 'Web UI Development' WHERE id = 12;")
    conn.execute("UPDATE books SET title = 'Intro to Machine Learning' WHERE id = 14;")
    conn.execute("UPDATE books SET title = 'Data Analysis with R' WHERE id = 15;")
    conn.execute("UPDATE books SET title = 'Artificial Intelligence' WHERE id = 22;")
    conn.execute("UPDATE books SET title = 'Huawei AI Technology Guide' WHERE id = 24;")
    conn.execute("UPDATE books SET title = 'AI Art & Generative Models' WHERE id = 26;")
    conn.execute("UPDATE books SET title = 'Hierarchical Clustering' WHERE id = 27;")
    conn.execute("UPDATE books SET title = 'Machine Learning Tutorial' WHERE id = 29;")
    conn.execute("UPDATE books SET title = 'Prompt Engineering Guide' WHERE id = 35;")
    conn.execute("UPDATE books SET title = 'Computer Vision with Python' WHERE id = 36;")
    conn.execute("UPDATE books SET title = 'ML with Python' WHERE id = 37;")
    conn.execute("UPDATE books SET title = 'PCI Data Security Standard' WHERE id = 40;")
    conn.execute("UPDATE books SET title = 'K-Means Clustering' WHERE id = 41;")
    conn.execute("UPDATE books SET title = 'NLP Fundamentals' WHERE id = 42;")
    conn.execute("UPDATE books SET title = 'Digital Forensics' WHERE id = 44;")
    conn.execute("UPDATE books SET title = 'Hacking Secret Ciphers' WHERE id = 45;")
    conn.execute("UPDATE books SET title = 'Math for ML' WHERE id = 47;")
    conn.execute("UPDATE books SET title = 'Mathematics for ML' WHERE id = 48;")
    conn.execute("UPDATE books SET title = 'AI and Librarianship' WHERE id = 49;")
    conn.execute("UPDATE books SET title = 'Hacking in Wired Networks' WHERE id = 50;")
    conn.execute("UPDATE books SET title = 'ML with Python' WHERE id = 51;")
    conn.execute("UPDATE books SET title = 'ML Research Papers' WHERE id = 52;")
    conn.execute("UPDATE books SET title = 'ML Power and Promise' WHERE id = 53;")
    conn.execute("UPDATE books SET title = 'Machine Learning Basics' WHERE id = 54;")
    conn.execute("UPDATE books SET title = 'Intro to Reinforcement Learning' WHERE id = 56;")
    conn.execute("UPDATE books SET title = 'AI Index Report 2024' WHERE id = 58;")
    conn.execute("UPDATE books SET title = 'Penetration Testing Guide' WHERE id = 63;")
    conn.execute("UPDATE books SET title = 'Deep Learning in Neural Networks' WHERE id = 64;")
    conn.execute("UPDATE books SET title = 'Computer Hacking' WHERE id = 65;")

    rows = conn.execute("SELECT id, title FROM books ORDER BY id;").fetchall()
    for book_id, title in rows:
        print(f"{book_id}: {title}")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
