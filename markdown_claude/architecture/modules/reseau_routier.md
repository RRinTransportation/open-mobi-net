---
role: architecture
lecteurs: agents qui touchent au réseau routier ou aux hypothèses de capacité
maj: 2026-09-25
---

# Module : réseau routier (OSM / AequilibraE)

Retour : [vue_ensemble](../vue_ensemble.md) · Voisins : [velo_marche.md](velo_marche.md), [transport_public.md](transport_public.md), [visualisation.md](visualisation.md)

## `AequilibraeBuilder` — [build_network/AequilibraeBuilder.py](../../../build_network/AequilibraeBuilder.py)

Hérite de `NetworkBuilder` (appel `super().__init__()` **sans arguments** → attributs par défaut, dont `target_crs`, cf. OBS-09).

| Méthode | Ligne | Rôle | Attributs produits |
|---|---|---|---|
| `__init__(networkbuilder, project_save_path)` | 16 | garde une référence au `NetworkBuilder` et à `study_area_polygon` | |
| `extract_network_from_osm()` | 27 | projet AequilibraE dans `%TEMP%/<uuid>`, `create_from_osm(model_area=polygone)` (téléchargement Overpass) | `links`, `nodes` |
| `_save_project(project)` | 45 | export GMNS + `link.csv`, `node.csv` dans `tmps_trial/` | fichiers |
| `preprocess_network()` | 55 | ajoute voies manquantes et capacités | `traffic_network` |
| `add_bike_network(...)` | 66 | → [velo_marche.md](velo_marche.md) | `bike_lanes`, `bike_nodes` |

- L'exception d'OSM est avalée ([ligne 32-36](../../../build_network/AequilibraeBuilder.py#L32-L36)) : message « VPN » puis poursuite (OBS-08).
- `traffic_network` **est** `links` (même objet, modifié en place).
- Le projet AequilibraE n'est pas conservé : le commentaire indique qu'on ne sait pas le recharger depuis les CSV.

## Hypothèses de complétion — [utils/network.py](../../../utils/network.py)

> README : « `utils/network.py` has been arbitrarily filled with assumptions that should be revised ».

| Élément | Ligne | Contenu |
|---|---|---|
| `LANE_CAPACITY_ASSUMPTIONS` | 6 | capacité par voie selon `link_type` (motorway 2000 … residential 600) |
| `CAPACITY_ASSUMPTIONS_BASED_ON_SPEED` | 26 | capacité par voie selon la vitesse **exacte** (clés 10, 15, 20, 30, 50, 70, 90, 110, 130) |
| `SPEED_ASSUMPTIONS_BASED_ON_TYPE` | 37 | vitesse par défaut selon `link_type` |
| `add_lanes_when_missing` / `add_lanes` | 70 / 115 | NaN+0 → (0,1) ou (1,0) ; NaN+NaN avec vitesses > 0 → (1,1) ; marque `added_lane` |
| `add_speed_when_missing` | 82 | remplit `speed_*` NaN/0 si `lanes_*` > 0 (liens `c`) — **non appelée par le pipeline actif** (OBS-04) |
| `add_capacity_on_car_links` / `estimate_capacity` | 102 / 135 | `capacity = lanes × capacité_par_voie` ; par type, sinon par vitesse (KeyError possible, OBS-05) |
| `load_shp_from_2154` | 64 | lecture SHP forcée en 2154 → 4326 (legacy vélo) |

Ordre réellement appliqué dans `preprocess_network` : `add_lanes_when_missing` → `add_capacity_on_car_links` (pas de complétion des vitesses).

## Anomalies connues des données OSM (README)

- Liens avec capacité et vitesse dans un sens mais `lanes` nul → toléré.
- `lanes_ab` et `lanes_ba` nuls/0 : si la vitesse existe → (1,1) supposé ; sinon on ne suppose rien. Visibles dans la couche « Car anomalies » ([visualisation.md](visualisation.md)). Illustration : [images/road_trafic_lanes_w_empty_features.png](../../../images/road_trafic_lanes_w_empty_features.png).

## Filtre « réseau voiture » (dupliqué à 3 endroits)

`modes` contient `c` **et** `link_type` ∉ {pedestrian, footway, service} : [PlottingMultimodal.py:84](../../../plotting/PlottingMultimodal.py#L84), [load_network/car.py:53](../../../load_network/car.py#L53), `anomalies.ipynb` (cellule 3, notebook supprimé depuis).
