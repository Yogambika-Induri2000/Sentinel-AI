import sys
import os
import psycopg2
import pandas as pd
from config.setting import settings

def initialize_database():
    print("Connecting to PostgreSQL database...")
    
    # Connect to PostgreSQL container
    conn = psycopg2.connect(settings.postgres_uri)
    cur = conn.cursor()

    print("1. Enabling pgvector extension...")
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    print("2. Creating relational 'videos' fact table...")
    cur.execute("""
        DROP TABLE IF EXISTS video_embeddings;
        DROP TABLE IF EXISTS videos;

        CREATE TABLE videos (
            video_id BIGINT PRIMARY KEY,
            claim_status VARCHAR(50),
            video_duration_sec INT,
            verified_status VARCHAR(50),
            author_ban_status VARCHAR(50),
            video_view_count BIGINT,
            video_like_count BIGINT,
            video_share_count BIGINT,
            video_download_count BIGINT,
            video_comment_count BIGINT,
            video_transcription_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    print("3. Creating 'video_embeddings' vector store table...")
    # Using 384 dimensions for all-MiniLM-L6-v2 / HuggingFace embeddings
    cur.execute("""
        CREATE TABLE video_embeddings (
            id SERIAL PRIMARY KEY,
            video_id BIGINT REFERENCES videos(video_id) ON DELETE CASCADE,
            transcription_chunk TEXT,
            embedding VECTOR(384),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    print("4. Creating B-Tree and HNSW Vector indexes...")
    # B-Tree indexes for fast SQL filter performance
    cur.execute("CREATE INDEX idx_claim_status ON videos(claim_status);")
    cur.execute("CREATE INDEX idx_author_ban ON videos(author_ban_status);")
    
    # HNSW Index for fast Vector Similarity Search
    cur.execute("""
        CREATE INDEX idx_vector_hnsw 
        ON video_embeddings 
        USING hnsw (embedding vector_cosine_ops);
    """)

    conn.commit()
    print("Database tables & indexes created successfully!")

    # Seed relational data from CSV
    seed_relational_data(conn, cur)

    cur.close()
    conn.close()

def seed_relational_data(conn, cur):
    print(f"Loading data from {settings.dataset_path}...")
    if not os.path.exists(settings.dataset_path):
        print(f"Error: {settings.dataset_path} not found.")
        return

    df = pd.read_csv(settings.dataset_path)
    
    # Clean data & handle NaN values
    df['claim_status'] = df['claim_status'].fillna('unknown')
    df['video_transcription_text'] = df['video_transcription_text'].fillna('')
    df = df.fillna(0)

    print(f"Seeding {len(df)} records into 'videos' table...")
    
    insert_query = """
        INSERT INTO videos (
            video_id, claim_status, video_duration_sec, verified_status, author_ban_status,
            video_view_count, video_like_count, video_share_count, video_download_count,
            video_comment_count, video_transcription_text
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (video_id) DO NOTHING;
    """

    records = [
        (
            int(row['video_id']),
            str(row['claim_status']),
            int(row['video_duration_sec']),
            str(row['verified_status']),
            str(row['author_ban_status']),
            int(row['video_view_count']),
            int(row['video_like_count']),
            int(row['video_share_count']),
            int(row['video_download_count']),
            int(row['video_comment_count']),
            str(row['video_transcription_text'])
        )
        for _, row in df.iterrows()
    ]

    cur.executemany(insert_query, records)
    conn.commit()
    print("Data seeding completed successfully!")

if __name__ == "__main__":
    initialize_database()