from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def get_recommendations(db, user_id, top_n=5):
    # Get all books
    all_books = db.execute("SELECT * FROM books").fetchall()
    all_books = [dict(b) for b in all_books]

    if not all_books:
        return []

    # Get books the user has borrowed
    borrowed = db.execute(
        "SELECT book_id FROM transactions WHERE user_id = ? AND status = 'borrowed'",
        (user_id,)
    ).fetchall()
    borrowed_ids = {row["book_id"] for row in borrowed}

    # Get all books the user ever interacted with
    history = db.execute(
        "SELECT DISTINCT book_id FROM transactions WHERE user_id = ?",
        (user_id,)
    ).fetchall()
    history_ids = {row["book_id"] for row in history}

    # Build corpus for TF-IDF
    corpus = []
    for book in all_books:
        text = f"{book['title']} {book['author']} {book['category']} {book['description'] or ''}"
        corpus.append(text)

    if len(corpus) < 2:
        return []

    # Fit TF-IDF
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(corpus)

    # Build index map
    book_index = {book["id"]: i for i, book in enumerate(all_books)}

    # Aggregate preference vector from user's history
    if history_ids:
        history_vectors = []
        for book_id in history_ids:
            if book_id in book_index:
                idx = book_index[book_id]
                history_vectors.append(tfidf_matrix[idx])

        if history_vectors:
            user_vector = np.mean(
                np.vstack([v.toarray() for v in history_vectors]),
                axis=0
            ).reshape(1, -1)
        else:
            return _popular_books(all_books, borrowed_ids, top_n)
    else:
        return _popular_books(all_books, borrowed_ids, top_n)

    # Compute similarities
    sim_scores = cosine_similarity(user_vector, tfidf_matrix)[0]

    # Score each book
    scored = []
    for i, book in enumerate(all_books):
        if book["id"] not in borrowed_ids:
            scored.append((book, float(sim_scores[i])))

    # Sort by similarity
    scored.sort(key=lambda x: x[1], reverse=True)

    recommendations = []
    for book, score in scored[:top_n]:
        recommendations.append({
            "id": book["id"],
            "title": book["title"],
            "author": book["author"],
            "category": book["category"],
            "image_url": book["image_url"],
            "price": book["price"],
            "similarity_score": round(score, 4)
        })

    return recommendations


def _popular_books(all_books, exclude_ids, top_n):
    """Fallback: return first N available books not in exclude list."""
    result = []
    for book in all_books:
        if book["id"] not in exclude_ids and book["available"]:
            result.append({
                "id": book["id"],
                "title": book["title"],
                "author": book["author"],
                "category": book["category"],
                "image_url": book["image_url"],
                "price": book["price"],
                "similarity_score": 0.0
            })
        if len(result) >= top_n:
            break
    return result
