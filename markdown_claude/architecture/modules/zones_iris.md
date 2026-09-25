---
role: architecture
lecteurs: agents qui travaillent sur le zonage / la future demande OD
maj: 2026-09-25
---

# Module : zones IRIS et agrégation

Retour : [vue_ensemble](../vue_ensemble.md) · Appelant : [orchestration.md](orchestration.md) (`_build_zones`) · Fichier : [load_network/iris.py](../../../load_network/iris.py)

## Appel depuis le pipeline

[MultiModalNetwork._build_zones](../../../build_network/MultiModalNetwork.py#L244) :
- `gdf_init_zones` = `networkbuilder.gdf` (IRIS de la zone d'étude) passé en `plane_projection` (2154) ;
- `cordon` = `study_area_polygon` déclaré en `target_crs` puis passé en 2154 ;
- `aggregate_iris_zones(target_n=target_n_zones, unique_id='DCOMIRIS', within=True, save_path=None)` ;
- ajoute `Zone_id = 0..n-1`, puis repasse les deux jeux en 4326 (`self.gdf_init_zones`, `self.gdf_agg_zones`).

## Algorithme (agrégation gloutonne)

| Fonction | Ligne | Rôle |
|---|---|---|
| `aggregate_iris_zones` | 181 | point d'entrée : prétraitement → découpage → scores initiaux → fusions jusqu'à `target_n` → sauvegarde optionnelle |
| `preprocess_iris_shp` | 142 | refuse le 4326 ; `unique_id` → int64 ; `area` (km²) ; `NEIGHBORS` (via `touches`) ; `CONTAINS` = [id] ; index = `unique_id` |
| `clip_gdf_with_polygon` | 160 | garde les zones `within` (ou `intersects`) le cordon, recalcule les voisins |
| `compute_score` | 16 | pour une zone : meilleur voisin minimisant `(s_i + s_j) / P_ij` (périmètre commun en km) ; option `agg_per_IRIS_type` (même `TYP_IRIS`) non exposée |
| `iteration_spatial_agg` | 51 | fusionne la paire aux **deux plus petits scores**, en supposant qu'il s'agit d'une paire réciproque (`assert`, OBS-11) ; met à jour voisins et scores ; remet `crs = 2154` |
| `get_dic_contained_index` / `get_index_from_iris_ids` | 123 / 137 | correspondance zone agrégée → index IRIS initiaux (pickle) — non appelées ; attendent `CONTAINS` sous forme de chaîne `"a,b,c"` et une colonne `CODE_IRIS` absente du SHP Lyon |
| `load_zones` | 11 | lit `Iris_lyon.shp` (casse différente du fichier réel) — non appelée |

Complexité : chaque fusion recalcule les scores des voisins (géométries `union` / `intersection`) → adapté à quelques centaines d'IRIS.

## Sorties

- `gdf_agg_zones` : colonnes IRIS de la première zone de chaque fusion + `area`, `NEIGHBORS`, `CONTAINS` (liste des `DCOMIRIS`), `best_score`, `best_neighbor`, `Zone_id`.
- Sauvegarde (`{save_path}/lyon_iris_agg{n}/lyon.shp`) : jamais déclenchée (OBS-16). Les colonnes liste (`NEIGHBORS`, `CONTAINS`) ne sont pas sérialisables telles quelles en SHP : à vérifier le jour où elle sera activée.

## Lien avec la phase 2 (OD)

Ce zonage est la base prévue des matrices OD (commit `cec3cff` : « Add IRIS zone and aggregated IRIS zone for OD »). Pas encore de centroïdes ni de connecteurs zone → réseau.
