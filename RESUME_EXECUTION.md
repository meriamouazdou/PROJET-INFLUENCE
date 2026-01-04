# 🎯 RÉSUMÉ RAPIDE - Comment Exécuter le Dashboard

## ⚡ Exécution Rapide (3 étapes)

### 1️⃣ Modifier le Mot de Passe Neo4j

**Dans `neo4j_import_and_metrics.py` (ligne 17) :**
```python
NEO4J_PASSWORD = "votre_mot_de_passe"  # ⚠️ MODIFIER
```

**Dans `dashboard_advanced.py` (ligne 126) :**
```python
password="votre_mot_de_passe"  # ⚠️ MODIFIER
```

### 2️⃣ Installer les Dépendances

```bash
pip install streamlit plotly pandas neo4j networkx
```

### 3️⃣ Exécuter le Pipeline

```bash
# Étape A : Import Neo4j et calcul des métriques
python neo4j_import_and_metrics.py

# Étape B : Lancer le dashboard
streamlit run dashboard_advanced.py
```

**C'est tout ! Le dashboard s'ouvre sur http://localhost:8501** 🚀

---

## 📁 Fichiers Fournis

1. **neo4j_import_and_metrics.py** - Script d'import et calcul des métriques
2. **dashboard_advanced.py** - Dashboard Streamlit avancé avec 6 pages
3. **requirements.txt** - Liste des dépendances Python
4. **GUIDE_INSTALLATION.md** - Guide complet d'installation
5. **requetes_cypher_utiles.cypher** - Collection de requêtes Cypher utiles

---

## 🎨 Fonctionnalités du Dashboard

### Page 1 : Vue d'Ensemble
- Métriques globales (utilisateurs, interactions, engagement, communautés)
- Distribution des types d'actions (pie chart)
- Top 10 influenceurs (bar chart)
- Évolution temporelle (line chart)

### Page 2 : Analyse des Influenceurs
- Classement PageRank et Betweenness
- Tableau détaillé avec métriques
- Graphique de corrélation
- Statistiques avancées

### Page 3 : Communautés
- Nombre de communautés détectées
- Distribution des tailles
- Influence par communauté
- Top influenceurs par communauté

### Page 4 : Visualisation du Graphe
- Graphe interactif NetworkX
- Nœuds colorés par communauté
- Taille proportionnelle au PageRank
- Statistiques du réseau (densité, degré moyen)

### Page 5 : Analyses Temporelles
- Évolution quotidienne avec double axe
- Distribution horaire
- Analyse par jour de la semaine
- Heatmap des actions

### Page 6 : Exploration Détaillée
- Profil utilisateur avec toutes les métriques
- Interactions entrantes et sortantes
- Distribution des types d'actions
- Réseau ego

---

## 🎨 Design Features

✨ **Design moderne avec gradient violet/bleu**
✨ **Cartes métriques avec effets hover**
✨ **Graphiques interactifs Plotly**
✨ **Navigation par sidebar**
✨ **Responsive et mobile-friendly**
✨ **Thème cohérent sur toutes les pages**

---

## ⚠️ Prérequis

- Neo4j Desktop démarré avec instance "meriam"
- Plugin GDS (Graph Data Science) installé
- Python 3.9+
- Fichiers CSV dans `~/projet-influence/datalake/gold/graph_edges/`

---

## 🐛 Dépannage Rapide

**Erreur de connexion Neo4j ?**
→ Vérifier que Neo4j est démarré et le mot de passe est correct

**Module non trouvé ?**
→ `pip install -r requirements.txt`

**Pas de données ?**
→ Vérifier que `spark/gold_export.py` a généré les CSV

**GDS non trouvé ?**
→ Installer le plugin dans Neo4j Desktop → Plugins

---

## 📊 Workflow Complet

```
1. Kafka Producer → 2. Spark Bronze → 3. Spark Silver → 4. Spark Gold
                                                              ↓
                    ← 8. Dashboard ← 7. Metrics CSV ← 5. Neo4j Import
                                                              ↓
                                                       6. GDS Algorithms
```

---

## 📞 Support

Pour plus de détails, consulter **GUIDE_INSTALLATION.md**

Pour les requêtes Neo4j, voir **requetes_cypher_utiles.cypher**

---

**Bon développement ! 🚀**
