import sys
import os
import time
import json
import random
import pandas as pd
from kafka import KafkaProducer

# Ensure project root is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from config.setting import settings

def start_event_producer():
    print(f"Checking dataset path: {settings.dataset_path}")
    if not os.path.exists(settings.dataset_path):
        print(f"❌ ERROR: Dataset file not found at '{settings.dataset_path}'! Please verify the path.")
        return

    print(f"Connecting to Kafka broker at {settings.kafka_bootstrap_servers}...")
    try:
        producer = KafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            acks="all"
        )
        print("✅ Successfully connected to Kafka Producer!")
    except Exception as e:
        print(f"❌ Failed to connect to Kafka: {e}")
        return

    df = pd.read_csv(settings.dataset_path)
    print(f"Loaded {len(df)} records from dataset. Starting live streaming simulation...\n")

    event_count = 0
    try:
        while True:
            sample_row = df.sample(1).iloc[0]
            
            payload = {
                "video_id": int(sample_row["video_id"]) + random.randint(1000000, 9999999),
                "claim_status": str(sample_row["claim_status"]) if pd.notna(sample_row["claim_status"]) else "unknown",
                "video_duration_sec": int(sample_row["video_duration_sec"]),
                "verified_status": str(sample_row["verified_status"]),
                "author_ban_status": str(sample_row["author_ban_status"]),
                "video_view_count": int(sample_row["video_view_count"]) if pd.notna(sample_row["video_view_count"]) else 0,
                "video_like_count": int(sample_row["video_like_count"]) if pd.notna(sample_row["video_like_count"]) else 0,
                "video_share_count": int(sample_row["video_share_count"]) if pd.notna(sample_row["video_share_count"]) else 0,
                "video_download_count": int(sample_row["video_download_count"]) if pd.notna(sample_row["video_download_count"]) else 0,
                "video_comment_count": int(sample_row["video_comment_count"]) if pd.notna(sample_row["video_comment_count"]) else 0,
                "video_transcription_text": str(sample_row["video_transcription_text"]) if pd.notna(sample_row["video_transcription_text"]) else "",
                "event_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            producer.send(settings.kafka_topic_events, value=payload)
            producer.flush()  # Force immediate flush to broker
            event_count += 1
            print(f"📡 [{event_count}] Streamed Event to Kafka: video_id={payload['video_id']} | claim_status={payload['claim_status']}")
            
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nStopping Producer...")
        producer.flush()
        producer.close()

if __name__ == "__main__":
    start_event_producer()