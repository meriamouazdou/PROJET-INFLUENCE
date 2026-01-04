// ============================================================================
// REQUÊTES CYPHER UTILES - PROJET INFLUENCE
// ============================================================================

// ----------------------------------------------------------------------------
// 1. VÉRIFICATION ET NETTOYAGE
// ----------------------------------------------------------------------------

// Compter tous les nœuds et relations
MATCH (n) RETURN count(n) AS total_nodes;
MATCH ()-[r]->() RETURN count(r) AS total_relationships;

// Voir un échantillon du graphe
MATCH (u:User)-[r:INTERACTS]->(u2:User)
RETURN u, r, u2
LIMIT 25;

// Nettoyer toute la base (ATTENTION : supprime tout !)
MATCH (n) DETACH DELETE n;

// ----------------------------------------------------------------------------
// 2. IMPORT MANUEL DES DONNÉES (si besoin)
// ----------------------------------------------------------------------------

// Import des utilisateurs depuis CSV
LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row
MERGE (u1:User {id: row.user_from})
MERGE (u2:User {id: row.user_to});

// Import des relations depuis CSV
LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row
MATCH (u1:User {id: row.user_from})
MATCH (u2:User {id: row.user_to})
CREATE (u1)-[:INTERACTS {
    action: row.action,
    timestamp: datetime(row.event_time)
}]->(u2);

// ----------------------------------------------------------------------------
// 3. VÉRIFICATION DES PLUGINS GDS
// ----------------------------------------------------------------------------

// Vérifier la version de GDS
CALL gds.version();

// Lister tous les graphes projetés
CALL gds.graph.list();

// Supprimer un graphe projeté
CALL gds.graph.drop('socialNetwork', false);

// ----------------------------------------------------------------------------
// 4. CRÉATION DU GRAPHE POUR GDS
// ----------------------------------------------------------------------------

// Projeter le graphe pour les algorithmes GDS
CALL gds.graph.project(
    'socialNetwork',
    'User',
    'INTERACTS',
    {
        relationshipProperties: 'action'
    }
);

// Vérifier les informations du graphe projeté
CALL gds.graph.list('socialNetwork')
YIELD graphName, nodeCount, relationshipCount;

// ----------------------------------------------------------------------------
// 5. CALCUL DES MÉTRIQUES - PAGERANK
// ----------------------------------------------------------------------------

// PageRank en mode stream (affichage seulement)
CALL gds.pageRank.stream('socialNetwork')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).id AS user, score
ORDER BY score DESC
LIMIT 10;

// PageRank en mode write (écriture dans la base)
CALL gds.pageRank.write('socialNetwork', {
    writeProperty: 'pagerank',
    maxIterations: 20,
    dampingFactor: 0.85
})
YIELD nodePropertiesWritten, ranIterations;

// Vérifier les résultats PageRank
MATCH (u:User)
RETURN u.id, u.pagerank
ORDER BY u.pagerank DESC
LIMIT 10;

// ----------------------------------------------------------------------------
// 6. CALCUL DES MÉTRIQUES - BETWEENNESS CENTRALITY
// ----------------------------------------------------------------------------

// Betweenness en mode stream
CALL gds.betweenness.stream('socialNetwork')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).id AS user, score
ORDER BY score DESC
LIMIT 10;

// Betweenness en mode write
CALL gds.betweenness.write('socialNetwork', {
    writeProperty: 'betweenness'
})
YIELD nodePropertiesWritten;

// Vérifier les résultats Betweenness
MATCH (u:User)
RETURN u.id, u.betweenness
ORDER BY u.betweenness DESC
LIMIT 10;

// ----------------------------------------------------------------------------
// 7. DÉTECTION DE COMMUNAUTÉS - LOUVAIN
// ----------------------------------------------------------------------------

// Louvain en mode stream
CALL gds.louvain.stream('socialNetwork')
YIELD nodeId, communityId
RETURN gds.util.asNode(nodeId).id AS user, communityId
ORDER BY communityId
LIMIT 20;

// Louvain en mode write
CALL gds.louvain.write('socialNetwork', {
    writeProperty: 'community_louvain',
    includeIntermediateCommunities: false
})
YIELD communityCount, modularity;

// Statistiques des communautés
MATCH (u:User)
WHERE u.community_louvain IS NOT NULL
RETURN u.community_louvain AS community, 
       count(*) AS size,
       avg(u.pagerank) AS avg_pagerank
ORDER BY size DESC;

// ----------------------------------------------------------------------------
// 8. DÉTECTION DE COMMUNAUTÉS - LABEL PROPAGATION
// ----------------------------------------------------------------------------

// Label Propagation en mode stream
CALL gds.labelPropagation.stream('socialNetwork')
YIELD nodeId, communityId
RETURN gds.util.asNode(nodeId).id AS user, communityId
ORDER BY communityId;

// Label Propagation en mode write
CALL gds.labelPropagation.write('socialNetwork', {
    writeProperty: 'community_lp',
    maxIterations: 10
})
YIELD communityCount, ranIterations;

// ----------------------------------------------------------------------------
// 9. AUTRES MÉTRIQUES UTILES
// ----------------------------------------------------------------------------

// Degré de chaque nœud (nombre de connexions)
MATCH (u:User)
WITH u, 
     size((u)-[:INTERACTS]->()) AS out_degree,
     size((u)<-[:INTERACTS]-()) AS in_degree
RETURN u.id, out_degree, in_degree, out_degree + in_degree AS total_degree
ORDER BY total_degree DESC
LIMIT 20;

// Closeness Centrality (proximité)
CALL gds.closeness.stream('socialNetwork')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).id AS user, score
ORDER BY score DESC
LIMIT 10;

// Triangle Count (nombre de triangles)
CALL gds.triangleCount.stream('socialNetwork')
YIELD nodeId, triangleCount
RETURN gds.util.asNode(nodeId).id AS user, triangleCount
ORDER BY triangleCount DESC
LIMIT 10;

// ----------------------------------------------------------------------------
// 10. REQUÊTES D'ANALYSE DU RÉSEAU
// ----------------------------------------------------------------------------

// Utilisateurs les plus influents (combinaison de métriques)
MATCH (u:User)
WHERE u.pagerank IS NOT NULL AND u.betweenness IS NOT NULL
RETURN u.id,
       u.pagerank,
       u.betweenness,
       u.community_louvain,
       (u.pagerank + u.betweenness/1000) AS influence_score
ORDER BY influence_score DESC
LIMIT 20;

// Analyser une communauté spécifique
MATCH (u:User)
WHERE u.community_louvain = 0  // Changer le numéro
RETURN u.id, u.pagerank, u.betweenness
ORDER BY u.pagerank DESC;

// Chemins les plus courts entre deux utilisateurs
MATCH path = shortestPath(
    (u1:User {id: 'user1'})-[*]-(u2:User {id: 'user10'})
)
RETURN path;

// Utilisateurs avec le plus d'interactions sortantes
MATCH (u:User)-[r:INTERACTS]->()
RETURN u.id, count(r) AS interactions_out
ORDER BY interactions_out DESC
LIMIT 10;

// Utilisateurs avec le plus d'interactions entrantes
MATCH (u:User)<-[r:INTERACTS]-()
RETURN u.id, count(r) AS interactions_in
ORDER BY interactions_in DESC
LIMIT 10;

// Distribution des actions (LIKE, SHARE, COMMENT)
MATCH ()-[r:INTERACTS]->()
RETURN r.action, count(r) AS count
ORDER BY count DESC;

// Interactions par type et par jour
MATCH ()-[r:INTERACTS]->()
WHERE r.timestamp IS NOT NULL
WITH r.action AS action, 
     date(r.timestamp) AS date
RETURN action, date, count(*) AS count
ORDER BY date, action;

// ----------------------------------------------------------------------------
// 11. EXPORT DES RÉSULTATS
// ----------------------------------------------------------------------------

// Exporter toutes les métriques des utilisateurs
MATCH (u:User)
RETURN u.id AS user,
       COALESCE(u.pagerank, 0) AS pagerank,
       COALESCE(u.betweenness, 0) AS betweenness,
       COALESCE(u.community_louvain, -1) AS community_louvain
ORDER BY u.pagerank DESC;

// Exporter les relations pour visualisation
MATCH (u1:User)-[r:INTERACTS]->(u2:User)
RETURN u1.id AS source,
       u2.id AS target,
       r.action AS action,
       r.timestamp AS timestamp
LIMIT 1000;

// ----------------------------------------------------------------------------
// 12. MAINTENANCE ET OPTIMISATION
// ----------------------------------------------------------------------------

// Créer des index pour améliorer les performances
CREATE INDEX user_id IF NOT EXISTS FOR (u:User) ON (u.id);
CREATE INDEX user_pagerank IF NOT EXISTS FOR (u:User) ON (u.pagerank);
CREATE INDEX user_community IF NOT EXISTS FOR (u:User) ON (u.community_louvain);

// Lister tous les index
SHOW INDEXES;

// Créer une contrainte d'unicité
CREATE CONSTRAINT user_id_unique IF NOT EXISTS 
FOR (u:User) REQUIRE u.id IS UNIQUE;

// Lister toutes les contraintes
SHOW CONSTRAINTS;

// Statistiques de la base de données
CALL db.stats.retrieve('GRAPH COUNTS');

// Informations sur l'utilisation de la mémoire
CALL dbms.queryJmx('org.neo4j:instance=kernel#0,name=Store file sizes');

// ----------------------------------------------------------------------------
// 13. VISUALISATION DANS NEO4J BROWSER
// ----------------------------------------------------------------------------

// Vue d'ensemble du réseau (limité pour performance)
MATCH (u:User)-[r:INTERACTS]->(u2:User)
RETURN u, r, u2
LIMIT 100;

// Colorier par communauté
MATCH (u:User)-[r:INTERACTS]->(u2:User)
WHERE u.community_louvain IS NOT NULL
RETURN u, r, u2
LIMIT 100;

// Afficher seulement les top influenceurs
MATCH (u:User)
WHERE u.pagerank > 0.01  // Ajuster le seuil
MATCH (u)-[r:INTERACTS]-(u2:User)
WHERE u2.pagerank > 0.01
RETURN u, r, u2;

// Réseau ego d'un utilisateur spécifique
MATCH (center:User {id: 'user1'})-[r:INTERACTS*1..2]-(other:User)
RETURN center, r, other;

// ----------------------------------------------------------------------------
// 14. DEBUGGING ET TESTS
// ----------------------------------------------------------------------------

// Vérifier si les propriétés existent
MATCH (u:User)
WHERE u.pagerank IS NOT NULL
RETURN count(u) AS users_with_pagerank;

MATCH (u:User)
WHERE u.betweenness IS NOT NULL
RETURN count(u) AS users_with_betweenness;

MATCH (u:User)
WHERE u.community_louvain IS NOT NULL
RETURN count(u) AS users_with_community;

// Vérifier les valeurs nulles
MATCH (u:User)
WHERE u.pagerank IS NULL OR u.betweenness IS NULL
RETURN u.id, u.pagerank, u.betweenness;

// Statistiques sur les métriques
MATCH (u:User)
WHERE u.pagerank IS NOT NULL
RETURN min(u.pagerank) AS min_pr,
       max(u.pagerank) AS max_pr,
       avg(u.pagerank) AS avg_pr,
       stdev(u.pagerank) AS std_pr;

// ============================================================================
// FIN DES REQUÊTES CYPHER
// ============================================================================

// NOTES :
// - Remplacer 'socialNetwork' par le nom de votre graphe projeté
// - Ajuster les LIMIT selon vos besoins
// - Pour les graphes très larges, utiliser des filtres WHERE
// - Consulter la documentation GDS : https://neo4j.com/docs/graph-data-science/
