---
role: architecture
lecteurs: agents qui touchent aux entrées/sorties ou aux projections
maj: 2026-09-25 (PLAN-002)
---

# Données, fichiers et systèmes de coordonnées

Retour : [vue_ensemble.md](vue_ensemble.md) · Flux : [pipeline_execution.md](pipeline_execution.md)

> `data/` est **ignoré par git** et en **lecture seule** pour les agents ([workflow](../gouvernance/workflow.md)).

## Arborescence `data/Lyon/` (constatée le 2026-09-25)

| Chemin | Contenu | Utilisé par le pipeline actif ? |
|---|---|---|
| `raw_data/net_car/shapefiles_sym/Iris_Lyon.shp` | 660 IRIS ; colonnes `DCOMIRIS, DEPCOM, IRIS, NOM_COM, NOM_IRIS, TYP_IRIS, area, DCOMIRIS_s, DEPCOM_str, territoire, territoi_1, Zone_I` ; **pas de .prj** (Lambert-93) | **oui** (zone d'étude + zones) |
| `raw_data/net_car/shapefiles_sym/{streets,nodes,ligne,emps,playableLinks}.shp`, `Lyon.qgs` | anciens réseaux / projet QGIS | non |
| `raw_data/net_bike/shapes/{links,nodes}_processed.shp` | réseau vélo prétraité ; **pas de .prj** ; emprise ≈ (832 473, 6 509 932) – (852 964, 6 528 970) ⇒ **Lambert-93** | **oui** (lu en 2154 depuis PLAN-001) |
| `raw_data/net_bike/shapes/bike_links.*`, `csvs/graph_{edges,nodes}.csv`, `net_bike.py` | sources vélo / script de prétraitement | non |
| `raw_data/net_pt/GTFS/lyon_tcl_gtfs.zip` (+ dossier dézippé, `rest/RUNS/...`) | GTFS TCL | oui, seulement au 1er lancement (OBS-02) |
| `raw_data/net_pt/GTFS/conversion_gtfs.py` | copie de `utils/conversion_gtfs.py` | non |
| `raw_data/net_pt/{lines/lines.shp, stops/stops.shp}` | cache GTFS extrait (WGS84, .prj présent) | **oui** (lecture à chaque run) |
| `raw_data/tmps_trial/{link,node,use_definition}.csv` | export du dernier run AequilibraE | écrit à chaque run |
| `raw_data/aequilibrae_lyon6/`, `aequilibrae_lyon_all/` | anciens exports AequilibraE (6e arr. / Lyon entier) | legacy (`load_network/car.py`) |
| `raw_data/all_shape/*.gpkg` | liens/nœuds par mode (b, c, t, w) | non |
| `raw_data/OD/OD_random.csv` | OD aléatoire (test) | non (phase 2) |
| `raw_data/net_walk/` | vide | — |
| `ready_input/demand/` | vide | phase 2 |
| `ready_input/networks/visualisation/aequilibrae_network_map.html` | carte exportée | non |
| `ready_input/networks/<nom>/` | **réseaux sauvegardés** (`network.gpkg` + `metadata.json`) | oui : `save()` / `load()` (PLAN-001) |

Fichiers à la racine du dépôt : `data.geojson` (dernier polygone dessiné, écrit par Streamlit, **suivi par git**), `selected_area.geojson` (ancien polygone, suivi, non utilisé), `temp_data.geojson` (temporaire, ignoré).

## Systèmes de coordonnées

| Code | Nom | Où il est utilisé |
|---|---|---|
| EPSG:2154 | Lambert-93 (mètres) | IRIS brut, vélo brut, **calculs métriques** : buffers et Hausdorff du map-matching, aires/périmètres IRIS (`plane_projection`) |
| EPSG:4326 | WGS84 (degrés) | `target_crs` : OSM/AequilibraE, GTFS, polygone Streamlit, Folium |

### Transitions de CRS dans le pipeline actif

| Étape | Entrée | Sortie | Remarque |
|---|---|---|---|
| `load_init_area` (IRIS) | SHP sans .prj → **forcé** `init_crs=2154` | 2154 | pas de `target_crs` passé dans `run()` |
| `_select_from_polygon` | 2154 | **4326** | seule branche qui reprojette `self.gdf` (OBS-06) |
| `add_bike_network` | SHP Lambert-93 déclaré 2154 | 4326 | OBS-01 corrigé (PLAN-001) |
| OSM (AequilibraE) | polygone 4326 | 4326 | |
| `MapMatchingPT2OSM` | 4326 | **2154** (non reprojeté en sortie) | sans gravité pour Folium qui reprojette ; à surveiller pour les usages en aval |
| `_build_zones` | IRIS → 2154 | 4326 | déclare le polygone d'étude en `target_crs` : juste seulement si l'étape 1 a produit du 4326 |

## Réseaux sauvegardés (PLAN-001)

Dossier `data/<Ville>/ready_input/networks/<AAAAMMJJ_HHMM ou nom>/` :

| Fichier | Contenu |
|---|---|
| `network.gpkg` | une couche par objet, **chacune dans son CRS d'origine** : `study_area`, `drawn_polygon`, `iris_selected`, `links` (= `traffic_network`), `nodes`, `bike_lanes`, `bike_nodes`, `pt_links_inside`, `pt_nodes_inside`, `pt_final_matches` (2154), `pt_final_links` (2154), `pt_bus_routes_init` (2154, diagnostic du map-matching, depuis PLAN-002), `zones_init`, `zones_agg`. Couches vides non écrites. Types de géométrie conservés (`promote_to_multi=False` ; une couche mixte est de type « Unknown ») |
| `metadata.json` | `format_version` (1), date, commit git (+ modifications non commitées), versions des librairies, `known_unfixed_issues`, paramètres de `MultiModalNetwork`, et par couche : CRS, nb de lignes, ordre des colonnes, noms d'index, colonnes liste (stockées en JSON dans le GPKG), couche vide ou non |

Code : [build_network/network_io.py](../../build_network/network_io.py) · Tests : [tests/test_network_io.py](../../tests/test_network_io.py).

## Formats et identifiants clés

- Liens AequilibraE : `link_id, a_node, b_node, direction, modes, link_type, lanes_ab/ba, speed_ab/ba, capacity_ab/ba, cycleway_left/right, geometry`. Voir [glossaire](glossaire.md).
- Lignes GTFS (`lines.shp`) : `trip_id, route_id, line_name, mode, mode_name, geometry` (issues de [SQL_query.py](../../build_network/build_pt_network/SQL_query.py)).
- Arrêts (`stops.shp`) : `stop_id, stop_name, lines, modes, route_ids, mode_name, geometry`.
- IRIS : clé `DCOMIRIS` (convertie en int64 et mise en index lors de l'agrégation).
