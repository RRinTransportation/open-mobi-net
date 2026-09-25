---
role: architecture
lecteurs: tous (à consulter au besoin)
maj: 2026-09-25
---

# Glossaire

Retour : [README](../README.md)

| Terme | Sens dans ce dépôt |
|---|---|
| **MMNE** | *Multi-Modal Network Extraction*, nom du projet. |
| **IRIS** | Découpage infra-communal de l'INSEE (≈ 2 000 habitants). Clé : `DCOMIRIS` ; type : `TYP_IRIS` (H habitat, A activité, D divers…). |
| **Zone d'étude** / `study_area_polygon` | Union (`union_all`) des IRIS retenus à l'étape 1 ; plus large que le polygone dessiné (tous les IRIS qui l'**intersectent**). |
| **Cordon** | Polygone de découpage passé à `aggregate_iris_zones` (ici = zone d'étude, en 2154). |
| **Zones agrégées** | Regroupement glouton d'IRIS adjacents jusqu'à `target_n_zones`, critère `(s_i + s_j) / P_ij` (aires / périmètre commun). |
| **AequilibraE** | Librairie de modélisation des transports ; ici : téléchargement OSM, import GTFS, export GMNS. |
| **GMNS** | *General Modeling Network Specification*, format CSV d'export des réseaux. |
| **Lien / nœud** | Arc / sommet du graphe routier (`link_id`, `a_node` → `b_node`). |
| **ab / ba** | Sens du lien : `ab` = de `a_node` vers `b_node`, `ba` = sens inverse. Colonnes `lanes_*`, `speed_*` (km/h), `capacity_*` (véh/h). |
| **`modes`** | Chaîne de codes AequilibraE autorisés sur le lien : `c` voiture, `b` vélo, `w` marche, `t` transport public (ex. `"cbw"`). |
| **`link_type`** | Type OSM `highway` (motorway, primary, residential, service, footway, cycleway, pedestrian…). |
| **`added_lane`** | Booléen ajouté par `add_lanes_when_missing` : vrai si le nombre de voies a été supposé. |
| **Anomalie de voies** | Lien voiture avec `lanes_ab` et `lanes_ba` nuls ou à 0 (couche « Car anomalies »). |
| **GTFS** | Format standard des horaires de transport public (routes, trips, stops, stop_times). Agence : `TCL`. |
| **`route_type` / `mode`** | Code GTFS du mode : 0 tramway, 1 métro, 3 bus, 6 funiculaire (`mode_mapping` dans `GTFSImporter`). |
| **pattern** | Séquence d'arrêts d'une route dans AequilibraE Transit (`pattern_id`). |
| **Map-matching** | Projection d'un tracé TC sur les liens OSM. Ici : liens candidats (buffer 10 m) + Dijkstra pondéré par similarité géométrique (Hausdorff + pénalité de longueur). |
| **`final_matches`** | Liens OSM retenus comme empruntés par au moins un bus. |
| **`final_pt_links`** | Tracés bus recomposés à partir des liens OSM (`sub_route_id, line_name, route_id, path_link_id`). |
| **`plane_projection`** | CRS métrique pour les calculs (EPSG:2154). `target_crs` = CRS de travail/affichage (EPSG:4326). |
| **MnMS** | Simulateur multimodal (LICIT) ; cible du script non branché `conversion_gtfs.py`. |
| **AVATAR** | Source de données de boucles de comptage (phase 2, calibrage). |
| **DUE** | *Deterministic User Equilibrium*, affectation de trafic (utilitaires dans `Ignore/notebooks/utils_aeq_due.py`). |
