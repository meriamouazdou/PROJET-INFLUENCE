"""
Script Neo4j : Import des données et calcul des métriques d'influence
Auteur : Projet INFLUENCE
Date : 2026-01-04
"""

from neo4j import GraphDatabase
import pandas as pd
import os
from pathlib import Path

# Configuration Neo4j
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "meriam2003"  # MODIFIER avec votre mot de passe

# Chemins
BASE_DIR = Path.home() / "projet-influence"
GOLD_EDGES_PATH = BASE_DIR / "datalake" / "gold" / "graph_edges"
METRICS_OUTPUT_PATH = BASE_DIR / "datalake" / "gold" / "metrics"
METRICS_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)


class Neo4jInfluenceAnalyzer:
    """Classe pour gérer l'import et l'analyse dans Neo4j"""
    
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
    def close(self):
        self.driver.close()
        
    def clear_database(self):
        """Nettoyer la base de données"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("✅ Base de données nettoyée")
            
    def create_constraints(self):
        """Créer les contraintes et index"""
        with self.driver.session() as session:
            try:
                session.run("CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE")
                print("✅ Contrainte User créée")
            except Exception as e:
                print(f"⚠️  Contrainte existe déjà : {e}")
                
    def import_graph_from_csv(self, csv_path):
        """Importer le graphe depuis CSV"""
        # Lire le CSV
        csv_files = list(csv_path.glob("*.csv"))
        if not csv_files:
            print(f"❌ Aucun fichier CSV trouvé dans {csv_path}")
            return
            
        df = pd.read_csv(csv_files[0])
        print(f"📊 Lecture de {len(df)} interactions depuis {csv_files[0].name}")
        
        with self.driver.session() as session:
            # Créer les nœuds utilisateurs
            users = set(df['user_from'].unique()) | set(df['user_to'].unique())
            print(f"👥 Création de {len(users)} utilisateurs...")
            
            for user in users:
                session.run(
                    "MERGE (u:User {id: $user_id})",
                    user_id=user
                )
            
            print("✅ Utilisateurs créés")
            
            # Créer les relations
            print(f"🔗 Création de {len(df)} relations...")
            for idx, row in df.iterrows():
                session.run("""
                    MATCH (u1:User {id: $user_from})
                    MATCH (u2:User {id: $user_to})
                    CREATE (u1)-[:INTERACTS {
                        action: $action,
                        timestamp: datetime($timestamp)
                    }]->(u2)
                """, 
                    user_from=row['user_from'],
                    user_to=row['user_to'],
                    action=row['action'],
                    timestamp=str(row['event_time'])
                )
                
                if (idx + 1) % 100 == 0:
                    print(f"   Progression : {idx + 1}/{len(df)}")
            
            print("✅ Relations créées")
            
    def compute_pagerank(self):
        """Calculer PageRank avec GDS"""
        with self.driver.session() as session:
            print("📊 Calcul de PageRank...")
            
            # Projeter le graphe
            try:
                session.run("CALL gds.graph.drop('socialNetwork', false)")
            except:
                pass
                
            session.run("""
                CALL gds.graph.project(
                    'socialNetwork',
                    'User',
                    'INTERACTS'
                )
            """)
            
            # Calculer PageRank et stocker
            session.run("""
                CALL gds.pageRank.write('socialNetwork', {
                    writeProperty: 'pagerank'
                })
            """)
            
            print("✅ PageRank calculé")
            
    def compute_betweenness(self):
        """Calculer Betweenness Centrality"""
        with self.driver.session() as session:
            print("📊 Calcul de Betweenness Centrality...")
            
            session.run("""
                CALL gds.betweenness.write('socialNetwork', {
                    writeProperty: 'betweenness'
                })
            """)
            
            print("✅ Betweenness calculé")
            
    def compute_communities(self):
        """Détecter les communautés avec Louvain"""
        with self.driver.session() as session:
            print("📊 Détection des communautés (Louvain)...")
            
            session.run("""
                CALL gds.louvain.write('socialNetwork', {
                    writeProperty: 'community_louvain'
                })
            """)
            
            print("✅ Communautés détectées")
            
    def export_metrics_to_csv(self, output_path):
        """Exporter les métriques vers CSV"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User)
                RETURN 
                    u.id AS user,
                    COALESCE(u.pagerank, 0.0) AS pagerank,
                    COALESCE(u.betweenness, 0.0) AS betweenness,
                    COALESCE(u.community_louvain, -1) AS community_louvain
                ORDER BY u.pagerank DESC
            """)
            
            data = [record.data() for record in result]
            df = pd.DataFrame(data)
            
            csv_file = output_path / "user_metrics.csv"
            df.to_csv(csv_file, index=False)
            
            print(f"✅ Métriques exportées vers {csv_file}")
            print(f"📊 {len(df)} utilisateurs avec métriques")
            
            # Afficher les top 5
            print("\n🏆 Top 5 Influenceurs (PageRank):")
            print(df.head(5).to_string(index=False))
            
            return df


def main():
    """Fonction principale"""
    print("="*70)
    print("🚀 IMPORT ET ANALYSE NEO4J - PROJET INFLUENCE")
    print("="*70)
    
    # Connexion à Neo4j
    analyzer = Neo4jInfluenceAnalyzer(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        # Étape 1 : Nettoyer la base
        print("\n📌 ÉTAPE 1 : Nettoyage de la base de données")
        analyzer.clear_database()
        
        # Étape 2 : Créer les contraintes
        print("\n📌 ÉTAPE 2 : Création des contraintes")
        analyzer.create_constraints()
        
        # Étape 3 : Importer le graphe
        print("\n📌 ÉTAPE 3 : Import du graphe depuis CSV")
        analyzer.import_graph_from_csv(GOLD_EDGES_PATH)
        
        # Étape 4 : Calculer PageRank
        print("\n📌 ÉTAPE 4 : Calcul de PageRank")
        analyzer.compute_pagerank()
        
        # Étape 5 : Calculer Betweenness
        print("\n📌 ÉTAPE 5 : Calcul de Betweenness Centrality")
        analyzer.compute_betweenness()
        
        # Étape 6 : Détecter les communautés
        print("\n📌 ÉTAPE 6 : Détection des communautés")
        analyzer.compute_communities()
        
        # Étape 7 : Exporter les métriques
        print("\n📌 ÉTAPE 7 : Export des métriques")
        analyzer.export_metrics_to_csv(METRICS_OUTPUT_PATH)
        
        print("\n" + "="*70)
        print("✅ TRAITEMENT TERMINÉ AVEC SUCCÈS")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        analyzer.close()


if __name__ == "__main__":
    main()
