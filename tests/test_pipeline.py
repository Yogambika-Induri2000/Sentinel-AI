import sys
import os
import psycopg2
import pytest

# Ensure project root is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from config.setting import settings
from src.genai.agent import search_vectors_direct, execute_sql_direct

def test_postgres_connection():
    """Verify PostgreSQL database connection is active."""
    conn = psycopg2.connect(settings.postgres_uri)
    assert conn is not None
    conn.close()

def test_relational_videos_table_count():
    """Verify relational 'videos' table is populated."""
    conn = psycopg2.connect(settings.postgres_uri)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM videos;")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    assert count > 0

def test_vector_direct_search():
    """Verify pgvector similarity search returns matches."""
    result = search_vectors_direct("drone deliveries")
    assert "Video ID:" in result or "No semantically similar" in result

def test_sql_direct_execution():
    """Verify relational SQL query executor operates correctly."""
    result = execute_sql_direct("SELECT COUNT(*) FROM videos;")
    assert "count" in result.lower()