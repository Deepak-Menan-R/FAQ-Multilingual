import pytest
import sqlite3
import redis
from app import app, DB_PATH

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for testing
    app.config["DATABASE"] = "db/test_faq.db"

    with app.test_client() as client:
        yield client

@pytest.fixture
def init_db():
    """Initialize test database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM faqs")
    cursor.execute("INSERT INTO users (name, email, password, role) VALUES ('Admin', 'admin@gmail.com', 'admin123', 'Admin')")
    conn.commit()
    conn.close()

def test_register(client):
    response = client.post("/register", data={"name": "Test User", "email": "test@gmail.com", "password": "test123"})
    assert response.status_code == 302  # Redirect to login

def test_login(client):
    response = client.post("/login", data={"email": "admin@gmail.com", "password": "admin123"})
    assert response.status_code == 302  # Redirect to admin panel

def test_invalid_login(client):
    response = client.post("/login", data={"email": "invalid@gmail.com", "password": "wrong"})
    assert b"Invalid Credentials" in response.data

def test_logout(client):
    client.post("/login", data={"email": "admin@gmail.com", "password": "admin123"})
    response = client.get("/logout", follow_redirects=True)
    assert b"Login" in response.data  # Redirected to login page

def test_add_faq(client):
    client.post("/login", data={"email": "admin@gmail.com", "password": "admin123"})
    response = client.post("/add_faq", data={"question": "Test Question?", "answer": "Test Answer"})
    assert response.status_code == 302  # Redirect to admin panel

def test_edit_faq(client, init_db):
    client.post("/login", data={"email": "admin@gmail.com", "password": "admin123"})
    client.post("/add_faq", data={"question": "Old Question?", "answer": "Old Answer"})
    
    # Fetch FAQ ID
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM faqs LIMIT 1")
    faq_id = cursor.fetchone()[0]
    conn.close()

    response = client.post(f"/update_faq/{faq_id}", data={"question": "Updated?", "answer": "Updated Answer"})
    assert response.status_code == 302  # Redirect to admin panel

def test_admin_access_restriction(client):
    response = client.get("/admin", follow_redirects=True)
    assert b"Login" in response.data  # Should redirect to login if not authenticated

def test_faq_translation(client):
    response = client.get("/api/faqs/?lang=es")  # Spanish translation
    assert response.status_code == 200
    assert b"Error" not in response.data  # Should not return errors

def test_redis_cache(client):
    cache_key = "faqs_en"
    redis_client = redis.StrictRedis(host="localhost", port=6379, db=0, decode_responses=True)
    redis_client.set(cache_key, "[('Cached Question?', 'Cached Answer')]")
    
    response = client.get("/api/faqs/?lang=en")
    assert b"Cached Question?" in response.data  # Should return cached response

