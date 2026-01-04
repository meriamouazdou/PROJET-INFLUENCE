"""
Dashboard Streamlit Avancé - Analyse des Réseaux d'Influence
Projet : PROJET-INFLUENCE
Auteur : Meriam Ouazdou
Date : 2026-01-04
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import networkx as nx
from neo4j import GraphDatabase
from pathlib import Path
import numpy as np
from datetime import datetime

# ============================================================================
# CONFIGURATION DE LA PAGE
# ============================================================================

st.set_page_config(
    page_title="Dashboard Influence - Analyse de Réseau Social",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# STYLES CSS PERSONNALISÉS
# ============================================================================

st.markdown("""
<style>
    /* Thème principal */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Cartes métriques */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    /* Titres */
    h1 {
        color: #1f2937;
        font-weight: 800;
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    h2 {
        color: #374151;
        font-weight: 700;
        border-bottom: 3px solid #667eea;
        padding-bottom: 10px;
    }
    
    h3 {
        color: #4b5563;
        font-weight: 600;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Boutons */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 10px 25px;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* Tables */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* Selectbox */
    .stSelectbox {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONNEXION NEO4J
# ============================================================================

class Neo4jConnection:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record.data() for record in result]

@st.cache_resource
def get_neo4j_connection():
    """Connexion Neo4j avec cache"""
    try:
        conn = Neo4jConnection(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="meriam2003"  # MODIFIER avec votre mot de passe
        )
        return conn
    except Exception as e:
        st.error(f"❌ Erreur de connexion à Neo4j : {e}")
        return None

# ============================================================================
# CHARGEMENT DES DONNÉES
# ============================================================================

BASE_DIR = Path.home() / "projet-influence"
EDGES_PATH = BASE_DIR / "datalake" / "gold" / "graph_edges" / "edges.csv"
METRICS_PATH = BASE_DIR / "datalake" / "gold" / "metrics" / "user_metrics.csv"

@st.cache_data
def load_edges():
    """Charger les données d'interactions"""
    try:
        df = pd.read_csv(EDGES_PATH)
        
        # Détecter la colonne temporelle
        time_col = None
        for col in ['timestamp', 'event_time', 'eventTime', 'event_time_utc']:
            if col in df.columns:
                time_col = col
                break
        
        if time_col:
            df['timestamp'] = pd.to_datetime(df[time_col], errors='coerce')
            df = df[~df['timestamp'].isna()].copy()
            df['date'] = df['timestamp'].dt.date
            df['hour'] = df['timestamp'].dt.hour
            df['day_name'] = df['timestamp'].dt.day_name()
        
        return df
    except Exception as e:
        st.error(f"❌ Erreur de chargement des edges : {e}")
        return pd.DataFrame()

@st.cache_data
def load_metrics():
    """Charger les métriques utilisateurs"""
    try:
        df = pd.read_csv(METRICS_PATH)
        
        # Assurer les colonnes nécessaires
        for col in ['pagerank', 'betweenness', 'community_louvain']:
            if col not in df.columns:
                df[col] = 0
        
        return df
    except Exception as e:
        st.error(f"❌ Erreur de chargement des métriques : {e}")
        return pd.DataFrame({'user': [], 'pagerank': [], 'betweenness': [], 'community_louvain': []})

@st.cache_data
def get_graph_data_from_neo4j():
    """Récupérer les données du graphe depuis Neo4j"""
    conn = get_neo4j_connection()
    if not conn:
        return None, None
    
    try:
        # Récupérer les nœuds
        nodes_query = """
        MATCH (u:User)
        RETURN u.id AS id, 
               COALESCE(u.pagerank, 0) AS pagerank,
               COALESCE(u.community_louvain, 0) AS community
        """
        nodes = conn.query(nodes_query)
        
        # Récupérer les liens
        edges_query = """
        MATCH (u1:User)-[r:INTERACTS]->(u2:User)
        RETURN u1.id AS source, u2.id AS target, r.action AS action
        LIMIT 500
        """
        edges = conn.query(edges_query)
        
        return pd.DataFrame(nodes), pd.DataFrame(edges)
    except Exception as e:
        st.error(f"❌ Erreur Neo4j : {e}")
        return None, None

# ============================================================================
# CHARGEMENT INITIAL
# ============================================================================

edges_df = load_edges()
metrics_df = load_metrics()

# ============================================================================
# SIDEBAR - NAVIGATION
# ============================================================================

st.sidebar.title("🌐 Navigation")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Choisir une vue",
    ["🏠 Vue d'ensemble", "📊 Analyse des Influenceurs", "👥 Communautés", 
     "🔗 Visualisation du Graphe", "📈 Analyses Temporelles", "🔍 Exploration Détaillée"]
)

st.sidebar.markdown("---")
st.sidebar.info(f"""
**Projet INFLUENCE**  
Analyse des réseaux d'influence  
Base de données : Neo4j  
Dashboard : Streamlit  

📅 {datetime.now().strftime('%d/%m/%Y')}
""")

# ============================================================================
# PAGE 1 : VUE D'ENSEMBLE
# ============================================================================

if page == "🏠 Vue d'ensemble":
    st.title("🌐 Tableau de Bord d'Influence - Réseaux Sociaux")
    
    st.markdown("""
    <div style='background: white; padding: 20px; border-radius: 15px; margin-bottom: 20px;'>
        <h3 style='color: #667eea;'>📋 À propos du projet</h3>
        <p>Ce dashboard analyse les interactions entre utilisateurs d'un réseau social pour identifier
        les influenceurs, détecter les communautés et visualiser la structure du réseau.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Métriques globales
    st.subheader("📊 Métriques Globales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_users = len(metrics_df)
        st.metric("👥 Utilisateurs", f"{total_users:,}", help="Nombre total d'utilisateurs dans le réseau")
    
    with col2:
        total_interactions = len(edges_df)
        st.metric("💬 Interactions", f"{total_interactions:,}", help="Nombre total d'interactions enregistrées")
    
    with col3:
        if total_interactions > 0:
            engagement = ((edges_df['action'] == 'LIKE').sum() + (edges_df['action'] == 'SHARE').sum()) / total_interactions * 100
        else:
            engagement = 0
        st.metric("📈 Engagement", f"{engagement:.1f}%", help="Taux d'engagement (likes + shares)")
    
    with col4:
        nb_communities = metrics_df[metrics_df['community_louvain'] >= 0]['community_louvain'].nunique()
        st.metric("🏘️ Communautés", f"{nb_communities}", help="Nombre de communautés détectées (Louvain)")
    
    st.markdown("---")
    
    # Graphiques côte à côte
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Distribution des Types d'Actions")
        action_counts = edges_df['action'].value_counts().reset_index()
        action_counts.columns = ['Action', 'Count']
        
        fig = px.pie(
            action_counts, 
            values='Count', 
            names='Action',
            color_discrete_sequence=px.colors.sequential.Purples_r,
            hole=0.4
        )
        fig.update_layout(
            height=400,
            showlegend=True,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🏆 Top 10 Influenceurs")
        top_influencers = metrics_df.nlargest(10, 'pagerank')
        
        fig = px.bar(
            top_influencers,
            x='pagerank',
            y='user',
            orientation='h',
            color='pagerank',
            color_continuous_scale='Purples'
        )
        fig.update_layout(
            height=400,
            showlegend=False,
            xaxis_title="Score PageRank",
            yaxis_title="Utilisateur",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Évolution temporelle
    st.subheader("📈 Évolution Temporelle des Interactions")
    
    if 'date' in edges_df.columns:
        timeline = edges_df.groupby('date').size().reset_index(name='count')
        
        fig = px.area(
            timeline,
            x='date',
            y='count',
            color_discrete_sequence=['#667eea']
        )
        fig.update_layout(
            height=300,
            xaxis_title="Date",
            yaxis_title="Nombre d'interactions",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# PAGE 2 : ANALYSE DES INFLUENCEURS
# ============================================================================

elif page == "📊 Analyse des Influenceurs":
    st.title("📊 Analyse des Influenceurs")
    
    st.markdown("""
    <div style='background: white; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
        <p>Identification des utilisateurs les plus influents basée sur les algorithmes <strong>PageRank</strong> 
        et <strong>Betweenness Centrality</strong> calculés par Neo4j GDS.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sélecteur de métrique
    col1, col2 = st.columns([1, 3])
    
    with col1:
        metric_choice = st.selectbox(
            "Métrique d'influence",
            ["PageRank", "Betweenness Centrality"],
            help="Choisir la métrique pour le classement"
        )
    
    with col2:
        top_n = st.slider("Nombre d'influenceurs à afficher", 5, 50, 20)
    
    # Affichage selon la métrique choisie
    if metric_choice == "PageRank":
        top_users = metrics_df.nlargest(top_n, 'pagerank')
        metric_col = 'pagerank'
        metric_label = 'Score PageRank'
    else:
        top_users = metrics_df.nlargest(top_n, 'betweenness')
        metric_col = 'betweenness'
        metric_label = 'Score Betweenness'
    
    # Graphique principal
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=top_users[metric_col],
        y=top_users['user'],
        orientation='h',
        marker=dict(
            color=top_users[metric_col],
            colorscale='Purples',
            showscale=True,
            colorbar=dict(title=metric_label)
        ),
        text=top_users[metric_col].round(4),
        textposition='auto',
    ))
    
    fig.update_layout(
        title=f"Top {top_n} Influenceurs - {metric_choice}",
        xaxis_title=metric_label,
        yaxis_title="Utilisateur",
        height=max(400, top_n * 20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tableau détaillé
    st.subheader("📋 Tableau Détaillé des Influenceurs")
    
    display_df = top_users[['user', 'pagerank', 'betweenness', 'community_louvain']].copy()
    display_df.columns = ['Utilisateur', 'PageRank', 'Betweenness', 'Communauté']
    display_df = display_df.round(6)
    
    st.dataframe(display_df, use_container_width=True, height=400)
    
    # Statistiques
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🥇 Top Influenceur", top_users.iloc[0]['user'])
    
    with col2:
        avg_score = top_users[metric_col].mean()
        st.metric(f"📊 {metric_label} Moyen", f"{avg_score:.6f}")
    
    with col3:
        std_score = top_users[metric_col].std()
        st.metric("📏 Écart-type", f"{std_score:.6f}")
    
    # Corrélation PageRank vs Betweenness
    st.subheader("🔗 Corrélation PageRank vs Betweenness")
    
    fig = px.scatter(
        metrics_df,
        x='pagerank',
        y='betweenness',
        color='community_louvain',
        hover_data=['user'],
        color_continuous_scale='Purples'
    )
    
    fig.update_layout(
        xaxis_title="PageRank",
        yaxis_title="Betweenness Centrality",
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# PAGE 3 : COMMUNAUTÉS
# ============================================================================

elif page == "👥 Communautés":
    st.title("👥 Analyse des Communautés")
    
    st.markdown("""
    <div style='background: white; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
        <p>Détection des communautés dans le réseau social à l'aide de l'algorithme <strong>Louvain</strong>.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Statistiques des communautés
    community_stats = (
        metrics_df[metrics_df['community_louvain'] >= 0]
        .groupby('community_louvain')
        .agg({
            'user': 'count',
            'pagerank': ['mean', 'sum'],
            'betweenness': 'mean'
        })
        .reset_index()
    )
    
    community_stats.columns = ['Communauté', 'Taille', 'PageRank Moyen', 'PageRank Total', 'Betweenness Moyen']
    community_stats = community_stats.sort_values('Taille', ascending=False)
    
    # Métriques
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🏘️ Nombre de Communautés", len(community_stats))
    
    with col2:
        largest = community_stats.iloc[0]['Taille'] if len(community_stats) > 0 else 0
        st.metric("👥 Plus Grande Communauté", int(largest))
    
    with col3:
        smallest = community_stats.iloc[-1]['Taille'] if len(community_stats) > 0 else 0
        st.metric("👤 Plus Petite Communauté", int(smallest))
    
    with col4:
        avg_size = community_stats['Taille'].mean() if len(community_stats) > 0 else 0
        st.metric("📊 Taille Moyenne", f"{avg_size:.1f}")
    
    # Visualisations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Distribution des Tailles")
        
        fig = px.bar(
            community_stats.head(15),
            x='Communauté',
            y='Taille',
            color='Taille',
            color_continuous_scale='Purples'
        )
        
        fig.update_layout(
            height=400,
            xaxis_title="ID Communauté",
            yaxis_title="Nombre d'utilisateurs",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🏆 Influence par Communauté")
        
        fig = px.scatter(
            community_stats,
            x='Taille',
            y='PageRank Total',
            size='PageRank Moyen',
            color='Betweenness Moyen',
            hover_data=['Communauté'],
            color_continuous_scale='Purples'
        )
        
        fig.update_layout(
            height=400,
            xaxis_title="Taille de la communauté",
            yaxis_title="PageRank Total",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Tableau détaillé
    st.subheader("📋 Détails des Communautés")
    st.dataframe(community_stats.round(4), use_container_width=True, height=400)
    
    # Top influenceurs par communauté
    st.subheader("🌟 Top Influenceurs par Communauté")
    
    selected_community = st.selectbox(
        "Sélectionner une communauté",
        sorted(metrics_df[metrics_df['community_louvain'] >= 0]['community_louvain'].unique())
    )
    
    community_members = metrics_df[metrics_df['community_louvain'] == selected_community].nlargest(10, 'pagerank')
    
    fig = px.bar(
        community_members,
        x='user',
        y='pagerank',
        color='pagerank',
        color_continuous_scale='Purples'
    )
    
    fig.update_layout(
        title=f"Top 10 Influenceurs - Communauté {selected_community}",
        xaxis_title="Utilisateur",
        yaxis_title="PageRank",
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# PAGE 4 : VISUALISATION DU GRAPHE
# ============================================================================

elif page == "🔗 Visualisation du Graphe":
    st.title("🔗 Visualisation Interactive du Graphe")
    
    st.markdown("""
    <div style='background: white; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
        <p>Visualisation du réseau social avec les nœuds (utilisateurs) et arêtes (interactions).</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Récupérer les données Neo4j
    with st.spinner("🔄 Chargement des données depuis Neo4j..."):
        nodes_df, edges_graph_df = get_graph_data_from_neo4j()
    
    if nodes_df is not None and edges_graph_df is not None:
        # Créer le graphe NetworkX
        G = nx.DiGraph()
        
        # Ajouter les nœuds
        for _, node in nodes_df.iterrows():
            G.add_node(
                node['id'],
                pagerank=node['pagerank'],
                community=node['community']
            )
        
        # Ajouter les arêtes
        for _, edge in edges_graph_df.iterrows():
            G.add_edge(edge['source'], edge['target'], action=edge['action'])
        
        # Layout
        pos = nx.spring_layout(G, k=0.5, iterations=50)
        
        # Créer les traces
        edge_trace = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace.append(
                go.Scatter(
                    x=[x0, x1, None],
                    y=[y0, y1, None],
                    mode='lines',
                    line=dict(width=0.5, color='#888'),
                    hoverinfo='none',
                    showlegend=False
                )
            )
        
        # Nœuds
        node_x = []
        node_y = []
        node_text = []
        node_color = []
        node_size = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(f"User: {node}<br>PageRank: {G.nodes[node]['pagerank']:.4f}")
            node_color.append(G.nodes[node]['community'])
            node_size.append(G.nodes[node]['pagerank'] * 1000 + 10)
        
        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers',
            hoverinfo='text',
            text=node_text,
            marker=dict(
                showscale=True,
                colorscale='Purples',
                color=node_color,
                size=node_size,
                colorbar=dict(
                    thickness=15,
                    title='Communauté',
                    xanchor='left',
                    titleside='right'
                ),
                line=dict(width=2, color='white')
            )
        )
        
        # Créer la figure
        fig = go.Figure(data=edge_trace + [node_trace])
        
        fig.update_layout(
            title="Graphe du Réseau Social",
            showlegend=False,
            hovermode='closest',
            height=700,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistiques du graphe
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🔗 Nœuds", G.number_of_nodes())
        
        with col2:
            st.metric("↔️ Arêtes", G.number_of_edges())
        
        with col3:
            density = nx.density(G)
            st.metric("📊 Densité", f"{density:.4f}")
        
        with col4:
            try:
                avg_degree = sum(dict(G.degree()).values()) / G.number_of_nodes()
                st.metric("📈 Degré Moyen", f"{avg_degree:.2f}")
            except:
                st.metric("📈 Degré Moyen", "N/A")
    
    else:
        st.warning("⚠️ Impossible de charger les données du graphe depuis Neo4j")

# ============================================================================
# PAGE 5 : ANALYSES TEMPORELLES
# ============================================================================

elif page == "📈 Analyses Temporelles":
    st.title("📈 Analyses Temporelles des Interactions")
    
    st.markdown("""
    <div style='background: white; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
        <p>Analyse de l'évolution des interactions dans le temps.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'date' in edges_df.columns:
        # Sélecteur de granularité
        granularity = st.radio("Granularité temporelle", ["Par jour", "Par heure", "Par jour de la semaine"], horizontal=True)
        
        if granularity == "Par jour":
            timeline = edges_df.groupby('date').agg({
                'action': 'count',
                'user_from': 'nunique'
            }).reset_index()
            timeline.columns = ['Date', 'Nombre d\'interactions', 'Utilisateurs actifs']
            
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig.add_trace(
                go.Scatter(
                    x=timeline['Date'],
                    y=timeline['Nombre d\'interactions'],
                    name="Interactions",
                    line=dict(color='#667eea', width=3),
                    fill='tonexty'
                ),
                secondary_y=False,
            )
            
            fig.add_trace(
                go.Scatter(
                    x=timeline['Date'],
                    y=timeline['Utilisateurs actifs'],
                    name="Utilisateurs actifs",
                    line=dict(color='#764ba2', width=2, dash='dot')
                ),
                secondary_y=True,
            )
            
            fig.update_xaxes(title_text="Date")
            fig.update_yaxes(title_text="Nombre d'interactions", secondary_y=False)
            fig.update_yaxes(title_text="Utilisateurs actifs", secondary_y=True)
            
            fig.update_layout(
                title="Évolution Quotidienne",
                height=500,
                hovermode='x unified',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        elif granularity == "Par heure":
            hourly = edges_df.groupby('hour').size().reset_index(name='count')
            
            fig = px.bar(
                hourly,
                x='hour',
                y='count',
                color='count',
                color_continuous_scale='Purples'
            )
            
            fig.update_layout(
                title="Distribution des Interactions par Heure",
                xaxis_title="Heure de la journée",
                yaxis_title="Nombre d'interactions",
                height=500,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        elif granularity == "Par jour de la semaine":
            if 'day_name' in edges_df.columns:
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                daily = edges_df.groupby('day_name').size().reset_index(name='count')
                daily['day_name'] = pd.Categorical(daily['day_name'], categories=day_order, ordered=True)
                daily = daily.sort_values('day_name')
                
                fig = px.bar(
                    daily,
                    x='day_name',
                    y='count',
                    color='count',
                    color_continuous_scale='Purples'
                )
                
                fig.update_layout(
                    title="Distribution par Jour de la Semaine",
                    xaxis_title="Jour",
                    yaxis_title="Nombre d'interactions",
                    height=500,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # Heatmap par action
        st.subheader("🔥 Heatmap des Actions par Jour")
        
        heatmap_data = edges_df.pivot_table(
            index='action',
            columns='date',
            aggfunc='size',
            fill_value=0
        )
        
        fig = px.imshow(
            heatmap_data,
            labels=dict(x="Date", y="Action", color="Nombre"),
            color_continuous_scale='Purples'
        )
        
        fig.update_layout(
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# PAGE 6 : EXPLORATION DÉTAILLÉE
# ============================================================================

elif page == "🔍 Exploration Détaillée":
    st.title("🔍 Exploration Détaillée d'un Utilisateur")
    
    st.markdown("""
    <div style='background: white; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
        <p>Explorez en détail les interactions et métriques d'un utilisateur spécifique.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sélection de l'utilisateur
    selected_user = st.selectbox(
        "🔎 Choisir un utilisateur",
        sorted(metrics_df['user'].unique()),
        help="Sélectionnez un utilisateur pour voir ses détails"
    )
    
    # Informations de l'utilisateur
    user_metrics = metrics_df[metrics_df['user'] == selected_user].iloc[0]
    
    st.subheader(f"👤 Profil : {selected_user}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 PageRank", f"{user_metrics['pagerank']:.6f}")
    
    with col2:
        st.metric("🔗 Betweenness", f"{user_metrics['betweenness']:.6f}")
    
    with col3:
        st.metric("🏘️ Communauté", int(user_metrics['community_louvain']))
    
    with col4:
        rank = metrics_df['pagerank'].rank(ascending=False)[user_metrics.name]
        st.metric("🏆 Classement", f"#{int(rank)}")
    
    # Interactions
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📤 Interactions Sortantes")
        user_out = edges_df[edges_df['user_from'] == selected_user]
        
        if len(user_out) > 0:
            st.metric("Nombre", len(user_out))
            
            action_dist = user_out['action'].value_counts()
            fig = px.pie(
                values=action_dist.values,
                names=action_dist.index,
                color_discrete_sequence=px.colors.sequential.Purples_r
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(
                user_out[['user_to', 'action', 'timestamp']].head(10),
                use_container_width=True
            )
        else:
            st.info("Aucune interaction sortante")
    
    with col2:
        st.subheader("📥 Interactions Entrantes")
        user_in = edges_df[edges_df['user_to'] == selected_user]
        
        if len(user_in) > 0:
            st.metric("Nombre", len(user_in))
            
            action_dist = user_in['action'].value_counts()
            fig = px.pie(
                values=action_dist.values,
                names=action_dist.index,
                color_discrete_sequence=px.colors.sequential.Purples_r
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(
                user_in[['user_from', 'action', 'timestamp']].head(10),
                use_container_width=True
            )
        else:
            st.info("Aucune interaction entrante")
    
    # Réseau ego
    st.subheader("🌐 Réseau Ego")
    
    ego_nodes = set(user_out['user_to'].unique()) | set(user_in['user_from'].unique())
    st.info(f"Cet utilisateur interagit avec {len(ego_nodes)} autres utilisateurs")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>📊 Dashboard PROJET-INFLUENCE | Développé avec Streamlit & Neo4j | 2026</p>
</div>
""", unsafe_allow_html=True)
