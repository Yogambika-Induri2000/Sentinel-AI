from pyspark.sql.types import StructType, StructField, StringType, LongType, IntegerType, TimestampType

# PySpark Schema for incoming TikTok video events from Kafka
tiktok_event_schema = StructType([
    StructField("video_id", LongType(), True),
    StructField("claim_status", StringType(), True),
    StructField("video_duration_sec", IntegerType(), True),
    StructField("verified_status", StringType(), True),
    StructField("author_ban_status", StringType(), True),
    StructField("video_view_count", LongType(), True),
    StructField("video_like_count", LongType(), True),
    StructField("video_share_count", LongType(), True),
    StructField("video_download_count", LongType(), True),
    StructField("video_comment_count", LongType(), True),
    StructField("video_transcription_text", StringType(), True),
    StructField("event_timestamp", StringType(), True)
])