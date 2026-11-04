import os
from pydantic import BaseModel

class Settings(BaseModel):
    # Kafka Configurations
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_topic_events: str = "tiktok-video-events"

    # PostgreSQL Configurations
    postgres_uri: str = os.getenv("POSTGRES_URI", "postgresql://admin:password@localhost:5432/sentinel_db")
    
    # Dataset Path
    dataset_path: str = "data/tiktok_dataset.csv"

settings = Settings()