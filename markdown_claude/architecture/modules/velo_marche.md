---
role: architecture
lecteurs: agents qui travaillent sur les modes actifs
maj: 2026-09-25 (PLAN-001)
---

# Module : vélo et marche

Retour : [vue_ensemble](../vue_ensemble.md) · Voisin : [reseau_routier.md](reseau_routier.md)

Il existe **deux sources parallèles** pour le vélo, qui ne sont pas reliées entre elles.

## Source A : OSM (via AequilibraE) → couches « Bike » et « Cycling Lanes »

Sous-réseaux extraits de `traffic_network` dans [PlottingMultimodal._extract_subnetworks](../../../plotting/PlottingMultimodal.py#L79) :

| Couche | Filtre |
|---|---|
| Bike | `modes` contient `b` et `link_type != footway` |
| Cycling Lanes | `modes` contient `b` et `link_type == cycleway` |
| Walk Only | `(modes contient w ET link_type == pedestrian) OU link_type == footway` (priorité des opérateurs, OBS-13) |

Version legacy plus riche (voies cyclables par sens via `cycleway_left/right`, exclusion des liens > 50 km/h) : `load_network_from_osm` dans [load_network/bike.py:6](../../../load_network/bike.py#L6), non branchée.

## Source B : shapefile prétraité → couches « own_loaded_bikes »

[AequilibraeBuilder.add_bike_network](../../../build_network/AequilibraeBuilder.py#L66), appelé depuis [MultiModalNetwork.py:195](../../../build_network/MultiModalNetwork.py#L195) :
- lit `net_bike/shapes/links_processed.shp` (colonnes `link_id, anode, bnode, is_bike`, 45 502 liens) et `nodes_processed.shp` (`node_id, X, Y`) via `load_init_area`, avec `init_crs='EPSG:2154'` (Lambert-93, fichiers sans .prj) ;
- **OBS-01 corrigé par PLAN-001** : avant, le fichier était déclaré en 4326 et le découpage était vide (0 lien au lieu de 1 234 sur la zone de `data.geojson`) ;
- affichée depuis PLAN-001 dans deux couches ([visualisation](visualisation.md)) : `own_loaded_bikes` (tous les liens) et `own_loaded_bikes is_bike` (`is_bike == 1`) ; sauvegardée dans les couches `bike_lanes` / `bike_nodes` du GPKG ;
- toujours **non rattachée au graphe OSM** et non utilisée pour du calcul (**OBS-20**).

La version legacy `load_network_from_preprocessed` ([load_network/bike.py:30](../../../load_network/bike.py#L30)) lisait les mêmes fichiers **en 2154**, ce qui confirme le CRS.

## Marche

- Uniquement depuis OSM (mode `w`) ; `data/.../net_walk/` est vide.
- Pas de connecteurs intermodaux (arrêts TC ↔ réseau piéton, parkings, etc.) : besoin exprimé dans les notes (voir [feuille_de_route](../../plan/feuille_de_route.md)).

## README « To do »

- « `arrows` from `bike` lack one direction » : les flèches de [add_network_layer](visualisation.md) sont tracées dans un seul sens (sens de digitalisation), quelle que soit la direction.
