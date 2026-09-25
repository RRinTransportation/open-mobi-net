---
role: architecture
lecteurs: agents qui modifient la carte
maj: 2026-09-25 (PLAN-002)
---

# Module : visualisation (Folium)

Retour : [vue_ensemble](../vue_ensemble.md) · Dossier : [plotting/](../../../plotting/)

> Fichiers **modifiés et non commités** au 2026-09-25 (ajout de la couche « anomalies », paramètres optionnels de `add_network_layer`).

## `PlottingMultimodal` — [plotting/PlottingMultimodal.py](../../../plotting/PlottingMultimodal.py)

Entrées : `aequilibraebuilder.traffic_network`, `.nodes`, `.bike_lanes` (si présent), `gtfs_network_builder.final_pt_links`, `.final_matches`, `.pt_bus_routes_init` (si présent), zones initiales et agrégées, liste `Layers` (défaut `["Car", "Bike", "Cycling Lanes", "Walk Only"]`).

| Méthode | Ligne | Rôle |
|---|---|---|
| `__init__` | 14 | stocke les données, appelle `_extract_subnetworks`, `_get_road_lane_without_direction`, `_get_own_loaded_bike_layers` et `_get_pt_bus_diagnostic_layers` |
| `_extract_subnetworks` | 97 | 7 couches potentielles (Car, Services Lanes, Original Car with direction, Added Car lane directions, Bike, Cycling Lanes, Walk Only), filtrées par `Layers` |
| `_get_own_loaded_bike_layers` | 120 | vélo **de nos shapefiles** (pas OSM) : `own_loaded_bikes` (tous les liens) et `own_loaded_bikes is_bike` (`is_bike == 1`) ; aucune couche si le vélo est absent ou vide |
| `_get_pt_bus_diagnostic_layers` | 133 | GTFS initial de bus en 2 couches (`matched` en vert, le reste en rouge ; statut, longueurs et écart de Hausdorff arrondis dans l'infobulle) + liens OSM retenus (`final_matches`) ; couches ignorées si absentes (réseaux sauvegardés avant PLAN-002) |
| `_get_road_lane_without_direction` | 154 | voiture avec `lanes_ab` et `lanes_ba` nuls ou 0 → `road_lane_anomalies` (requiert la couche « Car ») |
| `plotting(save=None)` | 32 | construit la carte (tuiles OSM), couches PT (GTFS initial, map-matché, liens OSM), « Car anomalies Lanes », « own_loaded_bikes … Lanes », zones, `LayerControl` ; `save` → HTML |

Utilise `network_gdf.unary_union` (déprécié, OBS-17) pour centrer la carte.

## Fonctions — [plotting/plotting_folium.py](../../../plotting/plotting_folium.py)

| Fonction | Ligne | Rôle |
|---|---|---|
| `plot_zones(map, init, agg)` | 10 | GeoJson des IRIS (colonnes `NOM_IRIS, DCOMIRIS_s, NOM_COM, DEPCOM, TYP_IRIS`) et des zones agrégées (`area, Zone_id`) |
| `draw_lane(map, gdf, name, color, tooltip)` | 32 | `FeatureGroup` « `{name} Lanes` » masqué par défaut + infobulle |
| `add_network_layer(...)` | 58 | liens (`draw_lane`) + nœuds (`CircleMarker` un par un) + flèches de direction (triangle à 25 % du lien, un seul sens) ; bug si `draw_arrows=False` (OBS-12) |
| `plot_layers_on_folium_map(layers, nodes, location, tiles, layercontrol)` | 161 | carte + `add_network_layer` par couche ; `assert` : aucune couche vide |

## Origine des couches vélo et TC

| Couche Folium | Source |
|---|---|
| `Bike Lanes`, `Cycling Lanes Lanes` (+ Nodes, Arrows) | réseau **OSM** (`traffic_network`, modes `b`) |
| `PT bus GTFS init - matched Lanes` / `- not matched Lanes` | tracés GTFS **initiaux** des bus (découpés par la zone) et résultat du map-matching (`pt_bus_routes_init`) |
| `PT bus map-matched Lanes` | bus **map-matchés** : tracés recomposés à partir des liens OSM (`final_pt_links`) ; s'appelait « PT Lanes » avant PLAN-002 |
| `PT bus OSM links used Lanes` | liens OSM retenus par le map-matching (`final_matches`) |
| `own_loaded_bikes Lanes`, `own_loaded_bikes is_bike Lanes` | **shapefiles vélo** `net_bike/shapes/*_processed.shp` |

## Points utiles

- Folium reprojette automatiquement les GeoDataFrame en 4326 (`folium/features.py`) : `final_pt_links` en 2154 s'affiche correctement.
- Les nœuds et flèches sont tracés **un marqueur par entité** : lent et lourd (notebooks de 4,7 à 38 Mo) sur de grandes zones.
- `assert` sur les couches vides : une petite zone sans piste cyclable, par exemple, fait échouer tout le tracé.
