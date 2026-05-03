# Influencer Analysis Pipeline
**Big Data & AI Engineering Project**

## Overview
End-to-end data pipeline for collecting, processing, and analyzing 
social media influencer networks. Built with a modern Big Data stack 
combining real-time streaming, graph database modeling, and 
interactive visualization across a 6-page analytics dashboard.

## Architecture
Kafka (Streaming) → Spark (Bronze → Silver → Gold)
↓
Neo4j (Graph Database)
↓
Streamlit Dashboard (6 pages)

## Dashboard Features
- **Overview** — global metrics, top 10 influencers, timeline
- **Influencer Analysis** — PageRank & Betweenness rankings
- **Communities** — Louvain detection, size distribution
- **Graph Visualization** — interactive NetworkX graph
- **Temporal Analysis** — daily/hourly heatmaps
- **Detailed Exploration** — individual user profiles & ego network

## Tech Stack
| Layer | Technologies |
|-------|-------------|
| Streaming | Apache Kafka |
| Processing | Apache Spark (PySpark) |
| Storage | Delta Lake (Bronze/Silver/Gold) |
| Graph Database | Neo4j + GDS Plugin |
| Algorithms | PageRank · Betweenness · Louvain |
| Visualization | Streamlit · Plotly · NetworkX |
| Language | Python 3.9+ |

## Graph Metrics Computed
- **PageRank** — influence scoring
- **Betweenness Centrality** — bridge detection
- **Louvain Community Detection** — cluster identification

## Quick Start
```bash
git clone https://github.com/meriamouazdou/PROJET-INFLUENCE
cd PROJET-INFLUENCE
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run Neo4j import & metrics
python neo4j_import_and_metrics.py

# Launch dashboard
streamlit run dashboard_advanced.py
```

## Requirements
- Python 3.9+
- Neo4j Desktop or Server (v5.x)
- Neo4j Graph Data Science Plugin
- Apache Kafka
- Apache Spark

