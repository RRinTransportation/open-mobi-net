---
role: architecture
lecteurs: agents qui ajoutent un paramètre, une ville ou un mode
maj: 2026-09-25 (PLAN-001)
---

# Module : configuration

Retour : [vue_ensemble](../vue_ensemble.md) · Consommateur : [orchestration.md](orchestration.md)

## Fichiers

- [config/Lyon_multimodal.py](../../../config/Lyon_multimodal.py) : un `argparse.ArgumentParser`, puis `args = parser.parse_args(args=[])` (ligne 39) → **valeurs par défaut uniquement**, la ligne de commande est ignorée.
- [utils/filtering.py](../../../utils/filtering.py) : `filter_args(args, cls)` garde les clés de `args` présentes dans la signature de `cls.__init__`.

## Paramètres et destination

| Paramètre | Défaut | Consommé par |
|---|---|---|
| `city` | `Lyon` | **personne** (filtré par `filter_args`) ; sert seulement à composer les défauts |
| `folder_path` | `data/Lyon/raw_data` | `MultiModalNetwork` (vélo, `tmps_trial`, GTFS) |
| `plane_projection` | `EPSG:2154` | `_build_zones` |
| `IRIS_folder_path`, `file_name` | `.../net_car/shapefiles_sym`, `Iris_Lyon.shp` | `NetworkBuilder` |
| `export_file` | `data.geojson` | polygone Streamlit |
| `init_crs`, `target_crs` | `EPSG:2154`, `EPSG:4326` | `NetworkBuilder`, `_build_zones` |
| `selection_from_polygon` | `True` (`type=bool` : piège, cf. OBS-16) | `NetworkBuilder.run` |
| `key_column`, `restricted_keys` | `None` (`type=list` : piège) | filtrage par attribut (ex. `NOM_COM`) |
| `shp_restriction_path` | `None` | restriction par un SHP (OBS-06) |
| `gtfs_folder_name`, `gtfs_zip_name`, `agency_name`, `transit_date` | `net_pt`, `lyon_tcl_gtfs.zip`, `TCL`, `2024-08-14` | `_build_pt_network` |
| `target_n_zones` | `5` | `_build_zones` |
| `save_path` | `None` | si renseigné, `build()` sauvegarde le réseau dans ce dossier (PLAN-001) |

## Paramètres codés en dur ailleurs (candidats à la config)

| Valeur | Où |
|---|---|
| Sous-chemins `net_bike/shapes`, `links_processed.shp`, `nodes_processed.shp`, `init_crs='EPSG:2154'` du vélo | [MultiModalNetwork.py:195-200](../../../build_network/MultiModalNetwork.py#L195-L200) |
| `project_save_path = {folder_path}/tmps_trial` | [MultiModalNetwork.py:191](../../../build_network/MultiModalNetwork.py#L191) |
| Dossier de sauvegarde par défaut `ready_input/networks/<AAAAMMJJ_HHMM>` | [MultiModalNetwork._default_save_path](../../../build_network/MultiModalNetwork.py#L166) |
| `unique_id='DCOMIRIS'`, `within=True` | [MultiModalNetwork.py:253-257](../../../build_network/MultiModalNetwork.py#L253-L257) |
| Buffer 10 m, epsilon 10 m, types exclus du map-matching | [MatMatchingPT2OSM.py:22,33,38](../../../build_network/build_pt_network/MatMatchingPT2OSM.py#L22) |
| `mode_mapping` GTFS | [GTFSImporter.py:75](../../../build_network/build_pt_network/GTFSImporter.py#L75) |
| Tables d'hypothèses voies/vitesses/capacités | [utils/network.py:6-61](../../../utils/network.py#L6-L61) |
| Liste des couches affichées | [PlottingMultimodal.py:17](../../../plotting/PlottingMultimodal.py#L17) |

## Ajouter une ville (état actuel)

Copier `config/Lyon_multimodal.py`, adapter les défauts, reproduire l'arborescence `data/<Ville>/raw_data/` ([donnees_et_crs.md](../donnees_et_crs.md)) et changer l'import dans le notebook. Le nom `Iris_*.shp`, la colonne `DCOMIRIS` et `mode_mapping` sont propres à Lyon/TCL.
