from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType
import os


# ==== 1. Chemins du Data Lake ====
BASE_DIR = os.path.expanduser("~/projet-influence")
BRONZE_PATH = os.path.join(BASE_DIR, "datalake", "bronze", "social_events")
CHECKPOINT_PATH = os.path.join(BASE_DIR, "datalake", "bronze", "checkpoints", "social_events")

# ==== 2. Schéma des événements Kafka ====
event_schema = StructType([
    StructField("user_from", StringType(), True),
    StructField("user_to", StringType(), True),
    StructField("action", StringType(), True),
    StructField("timestamp", StringType(), True),
])

# ==== 3. SparkSession + Delta ====
builder = (
    SparkSession.builder
    .appName("BronzeSocialEvents")
    .master("local[*]")
    # Activer Delta Lake
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    # Télécharger les jars nécessaires (Delta + Kafka)
    .config(
        "spark.jars.packages",
        "io.delta:delta-spark_2.13:4.0.0,"
        "org.apache.spark:spark-sql-kafka-0-10_2.13:3.5.1"
    )
)

spark = builder.getOrCreate()
spark.sparkContext.setLogLevel("WARN")

spark.sparkContext.setLogLevel("WARN")

print("✅ SparkSession créée avec Delta Lake.")
print(f"📂 Bronze path     : {BRONZE_PATH}")
print(f"📂 Checkpoint path : {CHECKPOINT_PATH}")

# ==== 4. Lecture du topic Kafka ====
kafka_df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "localhost:9092")
    .option("subscribe", "social-events")
    .option("startingOffsets", "latest")
    .load()
)

json_df = kafka_df.selectExpr("CAST(value AS STRING) AS value_str")

parsed_df = (
    json_df
    .select(from_json(col("value_str"), event_schema).alias("data"))
    .select("data.*")
)

# ==== 5. Écriture Delta (Zone Bronze) ====
query = (
    parsed_df.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", CHECKPOINT_PATH)
    .start(BRONZE_PATH)
)

print("🚀 Streaming en cours : Kafka -> Delta (Zone Bronze)")
print("   Ctrl+C pour stopper le job.")

query.awaitTermination()
