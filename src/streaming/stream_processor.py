import sys
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp

# Ensure project root is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from config.setting import settings
from src.streaming.schema import tiktok_event_schema

def start_spark_streaming():
    print("Initializing PySpark Session with Kafka & JDBC connectors...")
    
    # Initialize Spark Session configured for Kafka & Postgres JDBC
    spark = SparkSession.builder \
        .appName("SentinelAI-TikTokStreaming") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.postgresql:postgresql:42.7.2") \
        .master("local[*]") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")
    print(f"Subscribing to Kafka Topic: '{settings.kafka_topic_events}' at {settings.kafka_bootstrap_servers}...")

    # 1. Read Raw Streaming Stream from Kafka
    kafka_stream = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", settings.kafka_bootstrap_servers) \
        .option("subscribe", settings.kafka_topic_events) \
        .option("startingOffsets", "latest") \
        .load()

    # 2. Parse JSON Value Payloads using Schema
    parsed_stream = kafka_stream \
        .selectExpr("CAST(value AS STRING) as json_payload") \
        .select(from_json(col("json_payload"), tiktok_event_schema).alias("data")) \
        .select("data.*")

    # 3. Clean and Transform Payload
    cleaned_stream = parsed_stream \
        .filter(col("video_id").isNotNull()) \
        .withColumn("created_at", current_timestamp())

    # 4. Write Micro-Batches to PostgreSQL via JDBC
    def write_micro_batch_to_postgres(df, batch_id):
        count = df.count()
        if count > 0:
            print(f"⚡ Processing Micro-Batch #{batch_id} with {count} streaming records...")
            
            # Extract JDBC parameters
            jdbc_url = settings.postgres_uri.replace("postgresql://", "jdbc:postgresql://")
            
            df.write \
                .format("jdbc") \
                .option("url", jdbc_url) \
                .option("dbtable", "videos") \
                .option("user", "admin") \
                .option("password", "password") \
                .option("driver", "org.postgresql.Driver") \
                .mode("append") \
                .save()
            print(f"✅ Micro-Batch #{batch_id} committed to PostgreSQL 'videos' table.")

    # 5. Start Streaming Query
    query = cleaned_stream.writeStream \
        .foreachBatch(write_micro_batch_to_postgres) \
        .outputMode("append") \
        .start()

    print("🚀 PySpark Structured Streaming Pipeline active and listening for Kafka events!")
    query.awaitTermination()

if __name__ == "__main__":
    start_spark_streaming()