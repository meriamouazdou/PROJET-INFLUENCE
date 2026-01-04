# 🚀 Guide d'Installation et d'Exécution
## Dashboard Influence - PROJET-INFLUENCE

---

## 📋 Table des Matières

1. [Prérequis](#prérequis)
2. [Installation](#installation)
3. [Configuration Neo4j](#configuration-neo4j)
4. [Exécution du Pipeline](#exécution-du-pipeline)
5. [Lancement du Dashboard](#lancement-du-dashboard)
6. [Résolution de Problèmes](#résolution-de-problèmes)

---

## ✅ Prérequis

### Logiciels Nécessaires

- **Python 3.9+** installé
- **Neo4j Desktop** ou **Neo4j Server** (version 5.x recommandée)
- **Apache Kafka** (pour la collecte en temps réel)
- **Apache Spark** (pour le traitement des données)

### Vérification de l'Installation

```bash
# Vérifier Python
python3 --version

# Vérifier pip
pip3 --version
```

---

## 📦 Installation

### Étape 1 : Cloner ou Télécharger le Projet

```bash
cd ~/
git clone https://github.com/meriamouazdou/PROJET-INFLUENCE.git
cd PROJET-INFLUENCE
```

### Étape 2 : Créer un Environnement Virtuel (Recommandé)

```bash
# Créer l'environnement virtuel
python3 -m venv venv

# Activer l'environnement
# Sur macOS/Linux :
source venv/bin/activate

# Sur Windows :
venv\Scripts\activate
```

### Étape 3 : Installer les Dépendances

```bash
# Installer toutes les dépendances
pip install -r requirements.txt

# OU installer manuellement les packages essentiels
pip install streamlit plotly pandas neo4j networkx
```

---

## 🗄️ Configuration Neo4j

### Option 1 : Neo4j Desktop (Recommandé pour Développement)

1. **Ouvrir Neo4j Desktop**
2. **Vérifier votre instance** (vous avez déjà une instance "meriam")
3. **Noter les informations de connexion :**
   - URI : `bolt://localhost:7687`
   - Username : `neo4j`
   - Password : `[votre mot de passe]`

### Option 2 : Neo4j via Docker

```bash
docker run -d \
  --name neo4j-influence \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_PLUGINS='["graph-data-science"]' \
  neo4j:latest
```

### Configuration du Plugin GDS (Graph Data Science)

Si GDS n'est pas installé :

1. Dans Neo4j Desktop → Instance → Plugins
2. Installer "Graph Data Science Library"
3. Redémarrer l'instance

**Vérification :**
```cypher
CALL gds.version()
```

---

## ⚙️ Configuration des Scripts

### Modifier les Paramètres de Connexion

#### Dans `neo4j_import_and_metrics.py`

```python
# Ligne 15-17
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "votre_mot_de_passe"  # ⚠️ MODIFIER ICI
```

#### Dans `dashboard_advanced.py`

```python
# Ligne 124-126
conn = Neo4jConnection(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="votre_mot_de_passe"  # ⚠️ MODIFIER ICI
)
```

---

## 🚀 Exécution du Pipeline Complet

### Pipeline Étape par Étape

#### Étape 1 : Démarrer Kafka (Optionnel - si données en temps réel)

```bash
# Terminal 1 : Démarrer Zookeeper
zookeeper-server-start /path/to/zookeeper.properties

# Terminal 2 : Démarrer Kafka
kafka-server-start /path/to/kafka.properties

# Terminal 3 : Lancer le producteur
python kafka/producer.py
```

#### Étape 2 : Traitement Spark (Bronze → Silver → Gold)

```bash
# Terminal 1 : Streaming Bronze (si Kafka actif)
python spark/bronze_stream.py

# Terminal 2 : Traitement Silver
python spark/silver_batch.py

# Terminal 3 : Export Gold
python spark/gold_export.py
```

#### Étape 3 : Import Neo4j et Calcul des Métriques

```bash
# Exécuter le script d'import et calcul
python neo4j_import_and_metrics.py
```

**Ce script va :**
1. ✅ Nettoyer la base Neo4j
2. ✅ Créer les contraintes
3. ✅ Importer les nœuds et relations depuis CSV
4. ✅ Calculer PageRank
5. ✅ Calculer Betweenness Centrality
6. ✅ Détecter les communautés (Louvain)
7. ✅ Exporter les métriques vers CSV

**Sortie attendue :**
```
======================================================================
🚀 IMPORT ET ANALYSE NEO4J - PROJET INFLUENCE
======================================================================

📌 ÉTAPE 1 : Nettoyage de la base de données
✅ Base de données nettoyée

📌 ÉTAPE 2 : Création des contraintes
✅ Contrainte User créée

📌 ÉTAPE 3 : Import du graphe depuis CSV
📊 Lecture de XXX interactions depuis edges.csv
👥 Création de XX utilisateurs...
✅ Utilisateurs créés
🔗 Création de XXX relations...
✅ Relations créées

📌 ÉTAPE 4 : Calcul de PageRank
📊 Calcul de PageRank...
✅ PageRank calculé

📌 ÉTAPE 5 : Calcul de Betweenness Centrality
📊 Calcul de Betweenness Centrality...
✅ Betweenness calculé

📌 ÉTAPE 6 : Détection des communautés
📊 Détection des communautés (Louvain)...
✅ Communautés détectées

📌 ÉTAPE 7 : Export des métriques
✅ Métriques exportées vers ~/projet-influence/datalake/gold/metrics/user_metrics.csv
📊 XX utilisateurs avec métriques

🏆 Top 5 Influenceurs (PageRank):
...

======================================================================
✅ TRAITEMENT TERMINÉ AVEC SUCCÈS
======================================================================
```

---

## 📊 Lancement du Dashboard

### Méthode Recommandée

```bash
# Depuis le dossier du projet
streamlit run dashboard_advanced.py
```

### Configuration du Port (si 8501 est occupé)

```bash
streamlit run dashboard_advanced.py --server.port 8502
```

### Ouvrir le Dashboard

Le dashboard s'ouvre automatiquement dans votre navigateur à :
```
http://localhost:8501
```

---

## 🎨 Utilisation du Dashboard

### Navigation

Le dashboard comprend **6 pages** :

1. **🏠 Vue d'ensemble**
   - Métriques globales
   - Distribution des actions
   - Top 10 influenceurs
   - Évolution temporelle

2. **📊 Analyse des Influenceurs**
   - Classement PageRank
   - Classement Betweenness
   - Corrélations
   - Statistiques détaillées

3. **👥 Communautés**
   - Nombre de communautés
   - Distribution des tailles
   - Influence par communauté
   - Top influenceurs par communauté

4. **🔗 Visualisation du Graphe**
   - Graphe interactif NetworkX
   - Nœuds colorés par communauté
   - Taille proportionnelle au PageRank
   - Statistiques du réseau

5. **📈 Analyses Temporelles**
   - Évolution quotidienne
   - Distribution horaire
   - Heatmap des actions
   - Analyse par jour de la semaine

6. **🔍 Exploration Détaillée**
   - Profil utilisateur
   - Interactions entrantes/sortantes
   - Réseau ego
   - Métriques individuelles

---

## 🔧 Résolution de Problèmes

### Problème 1 : Erreur de Connexion Neo4j

**Erreur :**
```
❌ Erreur de connexion à Neo4j : Failed to establish connection
```

**Solution :**
1. Vérifier que Neo4j est démarré
2. Vérifier les credentials dans le code
3. Tester la connexion :
```bash
neo4j status
```

### Problème 2 : Plugin GDS Non Trouvé

**Erreur :**
```
There is no procedure with the name `gds.pageRank.write`
```

**Solution :**
1. Installer le plugin GDS dans Neo4j Desktop
2. Redémarrer Neo4j
3. Vérifier : `CALL gds.version()`

### Problème 3 : Fichier CSV Non Trouvé

**Erreur :**
```
❌ Aucun fichier CSV trouvé dans /datalake/gold/graph_edges
```

**Solution :**
1. Vérifier que Spark a généré le CSV :
```bash
ls ~/projet-influence/datalake/gold/graph_edges/
```
2. Exécuter `spark/gold_export.py` si nécessaire

### Problème 4 : Module Non Trouvé

**Erreur :**
```
ModuleNotFoundError: No module named 'streamlit'
```

**Solution :**
```bash
# Réinstaller les dépendances
pip install -r requirements.txt

# Ou installer le module manquant
pip install streamlit
```

### Problème 5 : Port Déjà Utilisé

**Erreur :**
```
OSError: [Errno 48] Address already in use
```

**Solution :**
```bash
# Utiliser un autre port
streamlit run dashboard_advanced.py --server.port 8502
```

---

## 📝 Commandes Rapides

### Tout Exécuter en Une Fois (après avoir les données)

```bash
# 1. Import Neo4j et calcul des métriques
python neo4j_import_and_metrics.py

# 2. Lancer le dashboard
streamlit run dashboard_advanced.py
```

### Vérifier que Tout Fonctionne

```bash
# Vérifier les fichiers générés
ls -lh ~/projet-influence/datalake/gold/metrics/

# Devrait afficher : user_metrics.csv
```

---

## 🎯 Checklist de Vérification

Avant de lancer le dashboard, vérifier :

- [ ] Neo4j est démarré et accessible
- [ ] Le plugin GDS est installé
- [ ] Les fichiers CSV existent dans `/datalake/gold/graph_edges/`
- [ ] Le mot de passe Neo4j est correctement configuré
- [ ] Les dépendances Python sont installées
- [ ] Le script `neo4j_import_and_metrics.py` s'est exécuté avec succès
- [ ] Le fichier `user_metrics.csv` existe dans `/datalake/gold/metrics/`

---

## 📞 Support

En cas de problème persistant :

1. Vérifier les logs Neo4j : Neo4j Desktop → Instance → Logs
2. Vérifier les logs Streamlit dans le terminal
3. Consulter la documentation :
   - Neo4j : https://neo4j.com/docs/
   - Streamlit : https://docs.streamlit.io/
   - Neo4j GDS : https://neo4j.com/docs/graph-data-science/

---

## 📊 Exemple de Flux Complet

```bash
# 1. Activer l'environnement virtuel
source venv/bin/activate

# 2. Vérifier Neo4j
neo4j status

# 3. Exécuter le pipeline Neo4j
python neo4j_import_and_metrics.py

# 4. Lancer le dashboard
streamlit run dashboard_advanced.py

# 5. Ouvrir http://localhost:8501 dans le navigateur
```

---

**Bon développement ! 🚀**
