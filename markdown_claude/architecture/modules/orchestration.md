---
role: architecture
lecteurs: agents qui modifient le déroulé global ou la sélection de zone
maj: 2026-09-25 (PLAN-002)
---

# Module : orchestration et zone d'étude

Retour : [vue_ensemble](../vue_ensemble.md) · Flux détaillé : [pipeline_execution](../pipeline_execution.md) · Config : [config.md](config.md)

## `MultiModalNetwork` — [build_network/MultiModalNetwork.py](../../../build_network/MultiModalNetwork.py)

Orchestrateur. Stocke ~17 paramètres (tous passés au constructeur via `filter_args`) et enchaîne :

| Méthode | Ligne | Délègue à | Retour / effet |
|---|---|---|---|
| `build()` | 56 | les 4 méthodes suivantes, puis `save(save_path)` si `save_path` | `(networkbuilder, aequilibraebuilder, gtfs_network_builder)` ; les mémorise aussi dans `self` |
| `save(path=None, overwrite=False)` | 73 | [network_io.save_network](../../../build_network/network_io.py) | dossier `network.gpkg` + `metadata.json` (défaut : `data/<Ville>/ready_input/networks/<AAAAMMJJ_HHMM>`) |
| `load(path)` | 112 | [network_io.load_network](../../../build_network/network_io.py) | même tuple que `build()` + zones ; **sans** Streamlit, OSM ni GTFS ; restaure les paramètres sauvegardés (affiche les différences) |
| `_new_networkbuilder()` | 170 | `NetworkBuilder(...)` | commun à `build` et `load` |
| `_build_working_area()` | 183 | `NetworkBuilder.run()` | `networkbuilder` |
| `_build_traffic_network(nb)` | 189 | `AequilibraeBuilder` → [reseau_routier](reseau_routier.md), [velo_marche](velo_marche.md) | `aequilibraebuilder` |
| `_build_pt_network(nb, aeq)` | 208 | `GTFSImporter`, `GTFSNetworkBuilder`, `MapMatchingPT2OSM` → [transport_public](transport_public.md) | `gtfs_network_builder` enrichi de `final_matches`, `final_pt_links`, `pt_bus_routes_init` (diagnostic) |
| `_build_zones(nb)` | 249 | `aggregate_iris_zones` → [zones_iris](zones_iris.md) | `self.gdf_init_zones`, `self.gdf_agg_zones` |

Remarques :
- Les résultats sont répartis entre la valeur de retour (3 builders) et des attributs de `self` (zones, et depuis PLAN-001 les 3 builders aussi, utilisés par `save`).
- Sauvegarde/chargement : format détaillé dans [donnees_et_crs.md](../donnees_et_crs.md). `load` construit `NetworkBuilder` et `AequilibraeBuilder` normalement (leur `__init__` est sans effet de bord) mais crée `GTFSNetworkBuilder` via `__new__` (son `__init__` relit tout le cache GTFS) : `pt_links`, `pt_nodes`, `unique_routes`, `pt_links_intersecting` ne sont donc pas disponibles après `load`. `pt_bus_routes_init` (diagnostic du map-matching, PLAN-002) est restauré s'il a été sauvegardé, sinon il vaut `None`.
- Tous les modes sont toujours construits (README « To do » : permettre un sous-ensemble de modes).
- Le bloc `__main__` (fin de fichier) n'est plus à jour : il ne passe pas `plane_projection` ni `target_n_zones` → `TypeError`.

## `NetworkBuilder` — [build_network/builder.py](../../../build_network/builder.py)

Sélectionne les IRIS de la zone d'étude. Fonctions de module réutilisées ailleurs :

| Fonction | Ligne | Rôle | Réutilisée par |
|---|---|---|---|
| `load_init_area(folder, file, crs, target_crs)` | 17 | lit un SHP, **force** son CRS, reprojette éventuellement | `AequilibraeBuilder.add_bike_network` |
| `restrict_area_from_filtering(gdf, col, keys)` | 29 | filtre attributaire | `_restrict_from_filtering` |
| `convert_gdf_to_study_area_polygon` | 35 | union + reprojection | `_restrict_to_study_area` |
| `spatial_mask(gdf, polygon)` | 42 | garde les entités qui **intersectent** | `_select_from_polygon`, `_restrict_to_study_area` |

`run()` (ligne 69) applique, dans l'ordre et de façon cumulative : polygone dessiné → filtre attributaire → SHP de restriction, puis `study_area_polygon = gdf.union_all()`.
Incohérences de CRS entre les branches : **OBS-06**.

## Sélection par polygone (Streamlit)

Communication **par fichiers**, entre deux processus :

```mermaid
sequenceDiagram
    participant P as NetworkBuilder (notebook)
    participant S as streamlit (sous-processus)
    P->>P: supprime data.geojson, écrit temp_data.geojson (IRIS en 4326)
    P->>S: Popen(streamlit run selection_from_streamlit_ui.py), env TEMP_GDF_PATH
    S->>S: carte folium + Draw ; l'utilisateur dessine un polygone
    S->>S: clic « Save polygon » → écrit data.geojson, tente de fermer l'onglet
    loop toutes les 1 s
        P->>P: data.geojson existe ?
    end
    P->>S: terminate()
    P->>P: spatial_mask(IRIS, polygone)
```

- UI : [selection_from_streamlit_ui.py](../../../build_network/polygon_selection/selection_from_streamlit_ui.py), fonction `get_polygon_from_streamlit_ui` (seul le **premier** polygone dessiné est retenu).
- Chemin du script relatif au cwd ([builder.py:102](../../../build_network/builder.py#L102)) → exécuter depuis la racine.
- Attente sans fin si la fenêtre est fermée sans sauvegarder : **OBS-07**.
- Le chemin d'export modifiable dans l'UI n'est pas lu par le parent (il attend toujours `export_file`).
