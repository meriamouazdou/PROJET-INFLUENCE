from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    upper,
    to_timestamp,
    date_format,
)
from pyspark.sql.types import StructType, StructField, StringType
import os

# ==== 1. Chemins du Data Lake ====
BASE_DIR = os.path.expanduser("~/projet-influence")
BRONZE_PATH = os.path.join(BASE_DIR, "datalake", "bronze", "social_events")
SILVER_PATH = os.path.join(BASE_DIR, "datalake", "silver", "social_events_clean")

# ==== 2. Création de la SparkSession (Delta uniquement, pas besoin de Kafka ici) ====
builder = (
    SparkSession.builder
    .appName("SilverSocialEvents")
    .master("local[*]")
    # Activer Delta Lake
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    # Télécharger automatiquement Delta si besoin
    .config("spark.jars.packages", "io.delta:delta-spark_2.13:4.0.0")
)

spark = builder.getOrCreate()
spark.sparkContext.setLogLevel("WARN")

print("✅ SparkSession Silver créée.")
print(f"📂 Bronze path : {BRONZE_PATH}")
print(f"📂 Silver path : {SILVER_PATH}")

# ==== 3. Lecture des données Bronze (Delta) ====
print("📥 Lecture des données depuis la Zone Bronze...")

bronze_df = (
    spark.read
    .format("delta")
    .load(BRONZE_PATH)
)

print(f"📊 Nombre de lignes en Bronze : {bronze_df.count()}")

# ==== 4. Nettoyage & enrichissement (Zone Silver) ====
#  - suppression des doublons
#  - actions en majuscules (LIKE / SHARE / COMMENT)
#  - conversion du timestamp en type Timestamp
#  - filtrage des lignes invalides
#  - ajout de colonnes date et heure

clean_df = (
    bronze_df
    .dropDuplicates(["user_from", "user_to", "action", "timestamp"])
    .withColumn("action", upper(col("action")))
    .withColumn("event_time", to_timestamp(col("timestamp"), "yyyy-MM-dd HH:mm:ss"))
    .dropna(subset=["user_from", "user_to", "action", "event_time"])
    .withColumn("event_date", date_format(col("event_time"), "yyyy-MM-dd"))
    .withColumn("event_hour", date_format(col("event_time"), "HH"))
)

print(f"📊 Nombre de lignes en Silver (après nettoyage) : {clean_df.count()}")

print("💾 Écriture des données nettoyées vers la Zone Silver (Delta)...")

(
    clean_df.write
    .format("delta")
    .mode("overwrite")  # réécrit la table Silver à chaque exécution
    .save(SILVER_PATH)
)

print("✅ Zone Silver mise à jour avec succès.")

spark.stop()
print("👋 SparkSession arrêtée.")
