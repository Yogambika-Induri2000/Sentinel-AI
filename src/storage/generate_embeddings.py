import sys
import os
import psycopg2
from sentence_transformers import SentenceTransformer
from psycopg2.extras import execute_values

# Ensure project root is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from config.setting import settings

def generate_and_store_embeddings():
    print("Connecting to PostgreSQL database...")
    conn = psycopg2.connect(settings.postgres_uri)
    cur = conn.cursor()

    # Load local open-source embedding model (384 dimensions)
    print("Loading SentenceTransformer model ('all-MiniLM-L6-v2')...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    print("Fetching non-empty video transcriptions from database...")
    cur.execute("""
        SELECT video_id, video_transcription_text 
        FROM videos 
        WHERE video_transcription_text IS NOT NULL 
          AND TRIM(video_transcription_text) != '';
    """)
    records = cur.fetchall()
    print(f"Retrieved {len(records)} transcripts to process.")

    # Process in batches of 500 to keep memory low
    batch_size = 500
    total_records = len(records)
    
    print("Generating embeddings and writing to 'video_embeddings' table...")
    for i in range(0, total_records, batch_size):
        batch = records[i:i + batch_size]
        video_ids = [r[0] for r in batch]
        texts = [r[1] for r in batch]

        # Generate dense 384-dim embeddings
        embeddings = model.encode(texts, show_progress_bar=False)

        # Prepare payload tuples for batch insert
        insert_data = [
            (v_id, text, embedding.tolist())
            for v_id, text, embedding in zip(video_ids, texts, embeddings)
        ]

        insert_query = """
            INSERT INTO video_embeddings (video_id, transcription_chunk, embedding)
            VALUES %s;
        """
        execute_values(cur, insert_query, insert_data, template="(%s, %s, %s::vector)")
        conn.commit()

        processed = min(i + batch_size, total_records)
        print(f"Processed {processed}/{total_records} records ({(processed/total_records)*100:.1f}%)")

    cur.close()
    conn.close()
    print("✅ All vector embeddings successfully generated and stored in pgvector!")

if __name__ == "__main__":
    generate_and_store_embeddings()