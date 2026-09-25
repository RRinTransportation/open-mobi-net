---
role: plan
lecteurs: utilisateur (validation), dev (exécution), auditeur (revue)
maj: 2026-09-25
statut: TERMINE
---

# PLAN-001 — Sauvegarde et chargement d'un réseau multimodal

Index : [plan/README.md](../../plan/README.md) · Origine : réponses A-03 et A-06 de l'[AUDIT-001](../../audit/AUDIT-001_exploration_initiale.md) · Jalon : **J0** de la [feuille de route](../../plan/feuille_de_route.md)
Fiches concernées : [orchestration](../../architecture/modules/orchestration.md), [config](../../architecture/modules/config.md), [donnees_et_crs](../../architecture/donnees_et_crs.md)

## 1. Objectif
Après `multi_modal_network.build()`, pouvoir **sauvegarder** le réseau sur disque, puis le **recharger** plus tard avec `multi_modal_network.load(path)`, **sans Streamlit, sans téléchargement OSM et sans import GTFS**. La cellule de visualisation du notebook doit fonctionner telle quelle après un `load`.

## 2. Décisions (validées le 2026-09-25 : toutes les propositions par défaut, D-1 à D-7)

Chaque ligne propose un choix par défaut. Il suffit de répondre « OK » ou de corriger.

| # | Décision | Proposition par défaut | Alternative |
|---|---|---|---|
| D-1 | Format | **GeoPackage** : un fichier `network.gpkg` avec une couche par objet, lisible dans QGIS, CRS conservé par couche. Plus un fichier `metadata.json` | GeoParquet (plus rapide, gère les listes nativement, moins pratique dans QGIS) |
| D-2 | Emplacement | `data/<Ville>/ready_input/networks/<nom>/` (le dossier existe déjà) | chemin libre uniquement |
| D-3 | Nom par défaut | horodatage `AAAAMMJJ_HHMM` si aucun nom n'est fourni | nom obligatoire |
| D-4 | API | `save(path)` et `load(path)` sur `MultiModalNetwork`, plus un argument `save_path` : s'il est renseigné, `build()` sauvegarde automatiquement à la fin | fonctions seules |
| D-5 | Retour de `load` | le **même tuple** que `build()` : `(networkbuilder, aequilibraebuilder, gtfs_network_builder)`. Remplit aussi `gdf_init_zones` et `gdf_agg_zones` | un nouvel objet résultat unique (plus propre, mais change le notebook) |
| D-6 | Paramètres au chargement | `load` restaure les paramètres enregistrés dans `metadata.json` (ils font foi) et signale les différences avec la config courante | ignorer les paramètres |
| D-7 | Correction d'OBS-01 incluse ? | **Oui** : une ligne (`init_crs='EPSG:2154'` pour le vélo), sinon les réseaux sauvegardés auront un vélo vide | non, traité plus tard |

## 3. Contenu sauvegardé

| Couche GPKG | Source (attribut) | Utilisée par |
|---|---|---|
| `study_area` | `networkbuilder.study_area_polygon` | zones, reconstruction |
| `drawn_polygon` | `export_file` (`data.geojson`) s'il existe | reconstruction à l'identique, choix des jeux de test |
| `iris_selected` | `networkbuilder.gdf` | — |
| `links`, `nodes` | `aequilibraebuilder.links` (= `traffic_network`), `.nodes` | plot, map-matching |
| `bike_lanes`, `bike_nodes` | `aequilibraebuilder.bike_*` | futur |
| `pt_links_inside`, `pt_nodes_inside` | `gtfs_network_builder.*` | futur |
| `pt_final_matches`, `pt_final_links` | `gtfs_network_builder.final_matches`, `.final_pt_links` | plot |
| `zones_init`, `zones_agg` | `multi_modal_network.gdf_init_zones`, `.gdf_agg_zones` | plot, phase 2 |

Non sauvegardé : le GTFS complet (`pt_links`, `pt_nodes`), qui reste en cache dans `net_pt/`, et le projet AequilibraE temporaire.

Contenu de `metadata.json` : version du format (`1`), date, commit git, paramètres, CRS, nombre de lignes et colonnes « liste » de chaque couche, versions de geopandas et d'aequilibrae, et **constats connus non corrigés** au moment de la sauvegarde (ex. `["OBS-03"]`), pour repérer les réseaux à reconstruire.

Chaque couche est enregistrée **dans son CRS actuel** (par exemple `pt_final_links` reste en 2154) : ce plan ne change aucun CRS, hors option D-7.

## 4. Périmètre
- **Inclus** : `plotting/PlottingMultimodal.py` (couches `own_loaded_bikes`, ajoutées à la demande de l'utilisateur le 2026-09-25) ; nouveau module `build_network/network_io.py` ; `build_network/MultiModalNetwork.py` (méthodes `save`, `load`, et `save_path` dans `build`) ; `config/Lyon_multimodal.py` (argument `--save_path`) ; `build_networks.ipynb` (une cellule markdown et une cellule de code « Charger un réseau sauvegardé ») ; `README.md` (usage) ; un script de test `tests/test_network_io.py` ; option D-7 : une ligne dans `MultiModalNetwork.py`.
- **Exclu** : toute autre correction (OBS-02 à 20), les autres modifications de `plotting/`, le nettoyage du dépôt, `load_network/*`.
- **Données** : écriture uniquement dans le dossier de sauvegarde choisi. Aucune modification de `raw_data/`.

## 5. Étapes

| # | Étape | Fichiers | Agent | Fait |
|---|---|---|---|---|
| 1 | `save_network(layers, path, parameters, overwrite)` / `load_network(path)`. Colonnes liste converties en JSON puis restaurées ; index restauré (noms compris) ; couches vides recréées depuis les métadonnées ; colonnes `object` mixtes converties (nombres → numérique, booléens → bool) ; `FileExistsError` si un réseau existe déjà (sauf `overwrite=True`) | `build_network/network_io.py` | dev | [x] |
| 2 | `MultiModalNetwork.save(path=None, overwrite=False)` | `MultiModalNetwork.py:71` | dev | [x] |
| 3 | `MultiModalNetwork.load(path)` → même tuple que `build()` + zones. `NetworkBuilder` et `AequilibraeBuilder` sont construits normalement (leur `__init__` n'a pas d'effet de bord) ; `GTFSNetworkBuilder` est créé **sans** `__init__` (qui relirait tout le cache GTFS) | `MultiModalNetwork.py:109` | dev | [x] |
| 4 | `build()` mémorise les 3 builders et appelle `save(save_path)` si `save_path` est renseigné ; `aggregate_iris_zones` n'écrit plus de SHP (`save_path=None`) ; argument `--save_path` | `MultiModalNetwork.py:56`, `config/Lyon_multimodal.py:39` | dev | [x] |
| 5 | (D-7) vélo lu en `EPSG:2154` | `MultiModalNetwork.py:199` | dev | [x] |
| 5b | Couches `own_loaded_bikes` et `own_loaded_bikes is_bike` | `plotting/PlottingMultimodal.py:102` | dev | [x] |
| 6 | Tests hors ligne : 3 tests (aller-retour des couches y compris géométries mixtes et Z ; pas d'écrasement silencieux ; `MultiModalNetwork.save/load` avec réseau et sous-processus interdits) | `tests/test_network_io.py` | dev | [x] |
| 7 | Bout en bout sur la zone de `data.geojson` (Streamlit contourné et `tmps_trial` redirigé vers un dossier temporaire, **dans le script de vérification seulement**) | script hors dépôt | dev | [x] |
| 8 | Notebook (3 cellules insérées après la construction : markdown, `SAVE_NETWORK`, `LOAD_PATH`) + README + fiches d'architecture | notebook, `README.md`, `markdown_claude/` | dev | [x] |
| 9 | Revue | — | auditeur | [x] (voir §10) |

## 6. Critères d'acceptation
- [x] `load(save(x))` identique pour les 12 couches du réseau réel (lignes, colonnes, CRS, index, géométries à 1e-9, **types de géométrie**, listes) — bout en bout, 2026-09-25.
- [x] Après `load` dans un **processus neuf**, la cellule de visualisation (non modifiée) donne la même carte qu'après `build` : mêmes 19 couches Folium, mêmes effectifs.
- [x] `load` sans réseau ni sous-processus : `socket.connect` et `subprocess.Popen` interdits pendant le chargement (test + bout en bout) ; durée ≈ 4 s.
- [x] ~~Ouverture dans QGIS~~ : **sans objet** (l'utilisateur travaille uniquement en Python / notebooks). Lecture GDAL/pyogrio vérifiée.
- [x] Couches `own_loaded_bikes` non vides : 1 234 liens (dont 294 `is_bike`), à côté de « Bike » (658, OSM) et « Cycling Lanes » (86, OSM).
- [x] `python tests/test_network_io.py` : 3/3 OK.
- [x] Fiches `architecture/` et README mis à jour.

## 7. Risques / points d'attention
- Colonnes `object` mixtes (`capacity_*`, `lanes_*`) : relues en `float` au lieu de `int`/`None`. Sans effet sur l'affichage.
- Les réseaux sauvegardés contiennent les défauts non corrigés (OBS-03, OBS-04), tracés dans `metadata.json` (`known_unfixed_issues`, constante `KNOWN_UNFIXED_ISSUES` de `network_io.py` à tenir à jour).
- `load` ne restaure pas `pt_links`, `pt_nodes`, `unique_routes` ni `pt_links_intersecting` de `GTFSNetworkBuilder` (non sauvegardés, inutiles en aval aujourd'hui).

## 8. Découvertes en cours de route (hors périmètre, non traitées)
- **D-a** : un calque issu d'un `clip` mélange `LineString` et `MultiLineString` ; le GPKG convertissait tout en `MultiLineString`. **Traité dans le périmètre** (écriture avec `promote_to_multi=False`) car nécessaire au critère d'aller-retour.
- **D-b** : sur la zone test, `pt_nodes_inside` = **0 arrêt** et `pt_links_inside` = 4 072 tronçons qui traversent la frontière → confirme par exécution l'effet d'**OBS-03**. Non corrigé.
- **D-c** : importer le code réécrit `build_network/__pycache__/MultiModalNetwork.cpython-312.pyc`, **suivi par git** (OBS-18, reporté) ; il apparaît donc comme modifié dans `git status`.
- **D-d** : écarts au plan : l'argument `--network_name` n'a pas été ajouté (redondant avec `save(path)` et le nom horodaté par défaut) ; le notebook reçoit **deux** cellules de code (sauvegarde désactivée par défaut `SAVE_NETWORK = False`, chargement `LOAD_PATH = None`) au lieu d'une, pour que l'exécution de haut en bas reste sans effet.

## 9. Validation
- Proposé le : 2026-09-25
- **Validé par l'utilisateur le : 2026-09-25** (« OK PLAN-001 », propositions D-1 à D-7 acceptées ; étape 5b ajoutée à sa demande dans le même message)

## 10. Revue (auditeur)
- Réalisée le 2026-09-25 **dans la même session que le développement** : ce n'est pas une relecture indépendante.
- Diff contrôlé : seuls les fichiers du périmètre sont modifiés (+ le `.pyc` suivi, D-c) ; aucune écriture dans `data/` (`tmps_trial` et `data.geojson` inchangés) ; artefacts d'espaces introduits par l'édition corrigés (diff minimal).
- Résultat : **OK**, avec une réserve : ouverture dans QGIS à confirmer par l'utilisateur.
- Confirmation de l'utilisateur le 2026-09-25 : sauvegarde, rechargement et affichage fonctionnent dans son notebook → `TERMINE`, archivé.
