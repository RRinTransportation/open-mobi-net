---
role: architecture
lecteurs: agents qui modifient ou déboguent le pipeline
maj: 2026-09-25 (PLAN-001)
---

# Déroulé d'exécution (qui appelle quoi)

Retour : [vue_ensemble.md](vue_ensemble.md) · Données : [donnees_et_crs.md](donnees_et_crs.md)

> Pré-requis : exécuter depuis la **racine du dépôt** (tous les chemins sont relatifs au dossier courant, cf. OBS-07).

## Cellule 1 de `build_networks.ipynb`

```python
filtered_args = filter_args(args, MultiModalNetwork)      # utils/filtering.py:4
multi_modal_network = MultiModalNetwork(**filtered_args)
networkbuilder, aequilibraebuilder, gtfs_network_builder = multi_modal_network.build()
```

### Arbre d'appels de `MultiModalNetwork.build()` ([MultiModalNetwork.py:56](../../build_network/MultiModalNetwork.py#L56))

```text
build()
├── _build_working_area()                                   :183
│   └── NetworkBuilder(...).run()                           builder.py:69
│       ├── load_init_area(IRIS shp, crs=2154)              builder.py:17   → gdf en 2154
│       ├── [selection_from_polygon] _select_from_polygon   builder.py:90
│       │   ├── écrit temp_data.geojson (IRIS en 4326)
│       │   ├── subprocess: streamlit run selection_from_streamlit_ui.py  (env TEMP_GDF_PATH)
│       │   │     └── get_polygon_from_streamlit_ui → écrit data.geojson au clic « Save polygon »
│       │   ├── boucle d'attente jusqu'à l'existence de data.geojson   (OBS-07)
│       │   └── spatial_mask(IRIS 4326, polygone) → self.gdf = IRIS qui INTERSECTENT le polygone
│       ├── [key_column & restricted_keys] restrict_area_from_filtering
│       ├── [shp_restriction_path] _restrict_to_study_area   (OBS-06)
│       └── self.study_area_polygon = self.gdf.union_all()   ← union des IRIS, pas le polygone dessiné
│
├── _build_traffic_network(networkbuilder)                  :189
│   └── AequilibraeBuilder(networkbuilder, project_save_path=raw_data/tmps_trial)
│       ├── extract_network_from_osm()     Project.new(tmp) → create_from_osm(study_area_polygon)   ⚠ réseau (OBS-08)
│       │   ├── _export_network → self.links, self.nodes
│       │   └── _save_project  → tmps_trial/{link,node}.csv + export GMNS
│       ├── preprocess_network()           utils.network.add_lanes_when_missing / add_capacity_on_car_links  (OBS-04)
│       │   └── self.traffic_network
│       └── add_bike_network(net_bike/shapes, init_crs='EPSG:2154')  → self.bike_lanes / bike_nodes  (OBS-01 corrigé, PLAN-001)
│
├── _build_pt_network(networkbuilder, aequilibraebuilder)   :204
│   ├── si net_pt/stops/stops.shp absent → GTFSImporter(...)    ⚠ chemin cassé (OBS-02), ~1 h, 2e téléchargement OSM
│   ├── GTFSNetworkBuilder(net_pt)   lit lines/lines.shp + stops/stops.shp
│   │   └── restrain_to_area_study(study_area_polygon) → pt_links_inside   (OBS-03)
│   └── MapMatchingPT2OSM().match_pt_to_osm(pt_links_inside, aequilibraebuilder)
│       └── bus uniquement (OBS-10) → final_matches (liens OSM), final_pt_links (lignes recomposées)
│
├── _build_zones(networkbuilder)                            :244
│   └── aggregate_iris_zones(IRIS en 2154, target_n=5, cordon=study_area, within=True, save_path=None)   load_network/iris.py:181
│       → self.gdf_init_zones, self.gdf_agg_zones (reprojetés en 4326, + Zone_id)
└── [save_path renseigné] save(save_path)                   :71   → network.gpkg + metadata.json
```

## Cellules « Save / load » (ajoutées par PLAN-001)

- `SAVE_NETWORK = False` → si `True` : `multi_modal_network.save()`.
- `LOAD_PATH = None` → si renseigné, **à la place de la cellule 1** : `MultiModalNetwork(**filter_args(args, …)).load(LOAD_PATH)` rend `networkbuilder, aequilibraebuilder, gtfs_network_builder` et remplit les zones, sans Streamlit, OSM ni GTFS.

## Cellule de visualisation

```text
PlottingMultimodal(aequilibraebuilder, gtfs_network_builder, gdf_init_zones, gdf_agg_zones)
├── _extract_subnetworks()               filtre traffic_network par modes/link_type → layers_to_plot
├── _get_road_lane_without_direction()   anomalies voiture (lanes_ab & lanes_ba nuls/0)
└── plotting()
    ├── plot_layers_on_folium_map → add_network_layer (liens + nœuds + flèches) par couche
    ├── draw_lane(final_pt_links, "PT")
    ├── draw_lane(anomalies, "Car anomalies")
    ├── draw_lane(bike_lanes, "own_loaded_bikes") et (is_bike == 1, "own_loaded_bikes is_bike")
    ├── plot_zones(init, agg)
    └── LayerControl
```

Détails : [visualisation.md](modules/visualisation.md).

## Effets de bord (fichiers écrits pendant un run)

| Fichier | Écrit par | Remarque |
|---|---|---|
| `temp_data.geojson` (racine) | `_select_from_polygon` | supprimé en fin d'étape ; ignoré par git |
| `data.geojson` (racine) | UI Streamlit | **suivi par git** → arbre toujours « modifié » (OBS-18) |
| `data/Lyon/raw_data/tmps_trial/*` | `AequilibraeBuilder._save_project` | écrasé à chaque run |
| `%TEMP%/<uuid>/` | projets AequilibraE temporaires | jamais nettoyés |
| `data/Lyon/raw_data/net_pt/{lines,stops}/` | GTFSImporter (théoriquement) | voir OBS-02 |
| `<dossier>/network.gpkg`, `metadata.json` | `MultiModalNetwork.save` | uniquement sur demande (`save()`, `SAVE_NETWORK`, `--save_path`) ; refuse d'écraser sans `overwrite=True` |
