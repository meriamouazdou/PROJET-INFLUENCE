import pathlib
import pandas as pd
import streamlit as st
import plotly.express as px

# ----- page config & style -----
st.set_page_config(page_title="Dashboard Influence", layout="wide")

st.markdown(
    """
    <style>
        /* titres plus grands */
        .css-1y4p8pa h1 { font-size: 40px; }
        /* cards KPI spacing */
        .metric-card { padding: 8px 20px; }
        /* tableau */
        .st-dataframe { box-shadow: 0 2px 6px rgba(0,0,0,0.06); border-radius:8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- 1. Chargement des données ----------
BASE_DIR = pathlib.Path.home() / "projet-influence"
EDGES_PATH = BASE_DIR / "datalake" / "gold" / "graph_edges" / "edges.csv"
METRICS_PATH = BASE_DIR / "datalake" / "gold" / "metrics" / "user_metrics.csv"

@st.cache_data
def load_edges():
    try:
        df = pd.read_csv(EDGES_PATH)
    except Exception as e:
        st.error(f"Impossible de lire edges.csv : {e}")
        st.stop()

    # Déterminer la bonne colonne temporelle
    time_col = None
    if "timestamp" in df.columns:
        time_col = "timestamp"
    elif "event_time" in df.columns:
        time_col = "event_time"
    elif "eventTime" in df.columns:
        time_col = "eventTime"
    elif "event_time_utc" in df.columns:
        time_col = "event_time_utc"

    if time_col is None:
        st.error(f"Aucune colonne temporelle trouvée dans edges.csv. Colonnes disponibles : {list(df.columns)}")
        st.stop()

    # On crée une colonne 'timestamp' commune pour le reste du code
    df["timestamp"] = pd.to_datetime(df[time_col], errors="coerce")
    # supprimer lignes où la conversion a échoué
    df = df[~df["timestamp"].isna()].copy()

    # Colonnes dérivées
    df["date"] = df["timestamp"].dt.date
    df["hour"] = df["timestamp"].dt.hour

    # Normaliser noms des colonnes (juste au cas où)
    df.columns = [c.strip() for c in df.columns]

    return df

@st.cache_data
def load_metrics():
    try:
        df = pd.read_csv(METRICS_PATH)
    except Exception as e:
        st.error(f"Impossible de lire user_metrics.csv : {e}")
        st.stop()
    # Assurer les colonnes attendues existent
    if "user" not in df.columns:
        st.error(f"user_metrics.csv doit contenir une colonne 'user'. Colonnes trouvées: {list(df.columns)}")
        st.stop()
    # compléter colonnes absentes pour éviter KeyError plus loin
    if "pagerank" not in df.columns:
        df["pagerank"] = 0
    if "betweenness" not in df.columns:
        df["betweenness"] = 0
    if "community_louvain" not in df.columns:
        df["community_louvain"] = -1
    return df

edges = load_edges()
metrics = load_metrics()

# ---------- 2. Titre & résumé ----------
st.title("Tableau de bord d'influence sur réseau social (Projet Big Data)")

st.markdown(
    """
Ce tableau de bord présente les principaux indicateurs décisionnels :
- **Top 10 des influenceurs** (PageRank, Neo4j GDS)
- **Taux d’engagement global** sur le réseau
- **Communautés principales** (Louvain)
- **Évolution du volume d’interactions dans le temps**
    """
)

# ---------- 3. Indicateurs globaux (cartes KPI) ----------
total_events = len(edges)
likes = int((edges.get("action") == "LIKE").sum())
shares = int((edges.get("action") == "SHARE").sum())
comments = int((edges.get("action") == "COMMENT").sum())

engagement_rate = 0.0
if total_events > 0:
    engagement_rate = (likes + shares) / total_events

nb_users = int(metrics["user"].nunique())

# nombre de communautés (Louvain) dans metrics (exclure -1)
if "community_louvain" in metrics.columns:
    nb_communities = int(metrics[metrics["community_louvain"] >= 0]["community_louvain"].nunique())
else:
    nb_communities = 0

col1, col2, col3, col4 = st.columns([1,1,1,1])

with col1:
    st.markdown("<div class='metric-card'><h4>Nombre d'utilisateurs</h4><h2>{}</h2></div>".format(nb_users), unsafe_allow_html=True)
with col2:
    st.markdown("<div class='metric-card'><h4>Nombre total d'interactions</h4><h2>{}</h2></div>".format(total_events), unsafe_allow_html=True)
with col3:
    st.markdown("<div class='metric-card'><h4>Taux d'engagement</h4><h2 style='color:#e76f51'>{:.1f}%</h2></div>".format(engagement_rate*100), unsafe_allow_html=True)
with col4:
    st.markdown("<div class='metric-card'><h4>Nombre de communautés (Louvain)</h4><h2 style='color:#2a9d8f'>{}</h2></div>".format(nb_communities), unsafe_allow_html=True)

st.divider()

# ---------- 4. Top 10 influenceurs (PageRank) ----------
st.subheader("Top 10 influenceurs (PageRank)")

top10 = metrics.sort_values("pagerank", ascending=False).head(10).reset_index(drop=True)
st.dataframe(top10[["user", "pagerank"]].round(6))

fig_top = px.bar(
    top10,
    x="user",
    y="pagerank",
    title="Top 10 influenceurs (PageRank)",
    labels={"pagerank": "Score PageRank", "user": "Utilisateur"},
    height=420,
)
fig_top.update_layout(margin=dict(l=0,r=0,t=40,b=0), template="plotly_white")
st.plotly_chart(fig_top, use_container_width=True)

# ---------- 5. Répartition des communautés ----------
st.subheader("Communautés principales (Louvain)")
if nb_communities > 0:
    community_sizes = (
        metrics[metrics["community_louvain"] >= 0]
        .groupby("community_louvain")["user"]
        .count()
        .rename("nb_users")
        .sort_values(ascending=False)
    )
    comm_df = community_sizes.reset_index()
    comm_df.columns = ["community", "nb_users"]
    fig_comm = px.bar(comm_df, x="community", y="nb_users", title="Nombre d'utilisateurs par communauté",
                      labels={"community": "Communauté", "nb_users": "NB utilisateurs"},
                      color="nb_users", color_continuous_scale="tealrose")
    fig_comm.update_layout(template="plotly_white", height=360)
    st.plotly_chart(fig_comm, use_container_width=True)
else:
    st.info("Aucune communauté détectée (colonne community_louvain manquante ou valeurs non valides).")

# ---------- 6. Évolution temporelle des interactions ----------
st.subheader("Évolution temporelle du nombre d'interactions")

grouping = st.radio("Granularité temporelle", ["Par jour", "Par heure"], horizontal=True)

if grouping == "Par jour":
    timeseries = edges.groupby("date")["action"].count().rename("events").reset_index()
    fig_ts = px.line(timeseries, x="date", y="events", markers=True, title="Interactions par jour")
    fig_ts.update_layout(xaxis_title="Date", yaxis_title="Nombre d'interactions", template="plotly_white")
    st.plotly_chart(fig_ts, use_container_width=True, height=400)
else:
    by_hour = edges.groupby(["date", "hour"])["action"].count().rename("events").reset_index()
    unique_dates = int(by_hour["date"].nunique()) if not by_hour.empty else 0
    if unique_dates <= 10 and unique_dates > 0:
        fig_hour = px.line(by_hour, x="hour", y="events", color="date",
                           title="Interactions par heure (séries par date)")
    else:
        mean_hour = by_hour.groupby("hour")["events"].mean().reset_index() if not by_hour.empty else pd.DataFrame({"hour":[],"events":[]})
        fig_hour = px.line(mean_hour, x="hour", y="events", markers=True,
                           title="Interactions moyennes par heure (sur toutes les dates)")
    fig_hour.update_layout(xaxis_title="Heure", yaxis_title="Nombre d'interactions", template="plotly_white")
    st.plotly_chart(fig_hour, use_container_width=True, height=420)

# ---------- 7. Détail d’un utilisateur (exploration) ----------
st.subheader("Exploration des interactions d'un utilisateur")

selected_user = st.selectbox("Choisir un utilisateur", sorted(metrics["user"].unique()))

# mini-cards (profil sommaire)
u_row = metrics[metrics["user"] == selected_user].iloc[0]
st.markdown(f"**{selected_user}** — PageRank: `{u_row.get('pagerank',0):.4f}` — Betweenness: `{u_row.get('betweenness',0):.4f}` — Community: `{u_row.get('community_louvain',-1)}`")

user_edges_out = edges[edges.get("user_from") == selected_user]
user_edges_in = edges[edges.get("user_to") == selected_user]

c1, c2 = st.columns(2)
with c1:
    st.markdown(f"**Interactions sortantes de {selected_user}**")
    if not user_edges_out.empty:
        st.dataframe(user_edges_out[["user_to", "action", "timestamp"]].reset_index(drop=True))
    else:
        st.write("Aucune interaction sortante.")
with c2:
    st.markdown(f"**Interactions entrantes vers {selected_user}**")
    if not user_edges_in.empty:
        st.dataframe(user_edges_in[["user_from", "action", "timestamp"]].reset_index(drop=True))
    else:
        st.write("Aucune interaction entrante.")
