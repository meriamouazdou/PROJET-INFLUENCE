from pyspark.sql import SparkSession
from pyspark.sql.functions import col
import os

# ==== 1. Chemins du Data Lake ====
BASE_DIR = os.path.expanduser("~/projet-influence")

SILVER_PATH = os.path.join(BASE_DIR, "datalake", "silver", "social_events_clean")
GOLD_EDGES_PATH = os.path.join(BASE_DIR, "datalake", "gold", "graph_edges")

# ==== 2. SparkSession (Delta seulement) ====
builder = (
    SparkSession.builder
    .appName("GoldExportEdges")
    .master("local[*]")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    .config("spark.jars.packages", "io.delta:delta-spark_2.13:4.0.0")
)

spark = builder.getOrCreate()
spark.sparkContext.setLogLevel("WARN")

print("✅ SparkSession Gold créée.")
print(f"📂 Silver path : {SILVER_PATH}")
print(f"📂 Gold edges path : {GOLD_EDGES_PATH}")

# ==== 3. Lecture Silver ====
print("📥 Lecture des données nettoyées (Zone Silver)...")
silver_df = (
    spark.read
    .format("delta")
    .load(SILVER_PATH)
)

print(f"📊 Lignes en Silver : {silver_df.count()}")

# ==== 4. Sélection des colonnes utiles pour le graphe ====
# On garde seulement ce qui sert au graphe
edges_df = (
    silver_df.select(
        col("user_from"),
        col("user_to"),
        col("action"),
        col("event_time"),
        col("event_date"),
        col("event_hour")
    )
)

print("📊 Exemple de lignes (edges) :")
for row in edges_df.limit(5).collect():
    print(row)

# ==== 5. Écriture en CSV (Zone Gold) ====
print("💾 Écriture des arêtes en CSV vers la Zone Gold...")

(
    edges_df
    .coalesce(1)                  # 1 fichier CSV pour simplifier l'import Neo4j
    .write
    .mode("overwrite")
    .option("header", "true")
    .csv(GOLD_EDGES_PATH)
)

print("✅ Export des arêtes terminé.")
spark.stop()
print("👋 SparkSession arrêtée.")
