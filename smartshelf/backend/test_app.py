import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import app, hash_password
from database import init_db, get_db, migrate_schema, seed_admin

@pytest.fixture(autouse=True)
def setup(monkeypatch, tmp_path):
    app.config["TESTING"] = True
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr("database.DB_PATH", db_path)
    init_db()
    db = get_db()
    seed_admin(db, hash_password)
    db.commit()
    db.close()
    yield

@pytest.fixture
def client():
    return app.test_client()

def auth_client(client, email="test@example.com", password="pass123", name="Test User"):
    client.post("/signup", json={"name": name, "email": email, "password": password})
    login = client.post("/login", json={"email": email, "password": password}).get_json()
    token = login["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}
    return headers, login["data"]["user"]

def test_signup_returns_token(client):
    res = client.post("/signup", json={
        "name": "Test User", "email": "test@example.com", "password": "pass123"
    })
    data = res.get_json()
    assert data["success"] is True
    assert "user" in data["data"]
    assert "token" in data["data"]

def test_signup_duplicate(client):
    client.post("/signup", json={
        "name": "A", "email": "dupe@example.com", "password": "pass"
    })
    res = client.post("/signup", json={
        "name": "A", "email": "dupe@example.com", "password": "pass"
    })
    assert res.get_json()["success"] is False

def test_login(client):
    headers, user = auth_client(client, "login@example.com", "mypass", "Login Test")
    assert user["email"] == "login@example.com"

def test_login_wrong_password(client):
    client.post("/signup", json={
        "name": "X", "email": "x@example.com", "password": "right"
    })
    res = client.post("/login", json={"email": "x@example.com", "password": "wrong"})
    assert res.get_json()["success"] is False

def test_books(client):
    res = client.get("/books")
    data = res.get_json()
    assert data["success"] is True
    assert len(data["data"]["books"]) > 0

def test_borrow_return(client):
    headers, user = auth_client(client, "borrow@example.com")
    res = client.post("/borrow", json={"book_id": 1}, headers=headers)
    data = res.get_json()
    assert data["success"] is True
    assert "due_date" in data["data"]

    res = client.post("/return", json={"book_id": 1}, headers=headers)
    assert res.get_json()["success"] is True

def test_borrow_requires_auth(client):
    res = client.post("/borrow", json={"book_id": 1})
    assert res.status_code == 401

def test_history(client):
    headers, user = auth_client(client, "hist@example.com")
    client.post("/borrow", json={"book_id": 2}, headers=headers)

    res = client.get("/history", headers=headers)
    data = res.get_json()
    assert data["success"] is True
    assert len(data["data"]["history"]) >= 1

def test_recommendations(client):
    headers, user = auth_client(client, "rec@example.com")
    res = client.get("/recommendations", headers=headers)
    data = res.get_json()
    assert data["success"] is True
    assert "recommendations" in data["data"]

def test_overdue(client):
    headers, user = auth_client(client, "overdue@example.com")
    client.post("/borrow", json={"book_id": 3}, headers=headers)
    res = client.get(f"/overdue/{user['id']}", headers=headers)
    assert res.get_json()["success"] is True

def test_admin_login(client):
    res = client.post("/login", json={
        "email": "admin@smartshelf.com", "password": "admin123"
    })
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["user"]["is_admin"] is True

def test_admin_add_delete_book(client):
    res = client.post("/login", json={
        "email": "admin@smartshelf.com", "password": "admin123"
    })
    headers = {"Authorization": f"Bearer {res.get_json()['data']['token']}"}

    add = client.post("/admin/books", json={
        "title": "Test Admin Book",
        "author": "Admin Author",
        "category": "Web Development",
        "image_url": "https://example.com/img.jpg",
        "description": "A test book",
    }, headers=headers)
    assert add.get_json()["success"] is True
    book_id = add.get_json()["data"]["book"]["id"]

    delete = client.delete(f"/admin/books/{book_id}", headers=headers)
    assert delete.get_json()["success"] is True
