---
role: plan
lecteurs: utilisateur (validation), dev (exécution), auditeur (revue)
maj: 2026-09-25
statut: EN_COURS (revue OK, en attente de confirmation utilisateur)
---

# PLAN-002 — Afficher le GTFS initial et le map-matché des bus (diagnostic)

Index : [plan/README.md](README.md) · Origine : demande de l'utilisateur du 2026-09-25 et [AUDIT-002 — map-matching des bus](../audit/AUDIT-002_map_matching_bus.md) · Jalon : **J1 — map-matching bus** de la [feuille de route](feuille_de_route.md)
Fiches concernées : [transport_public](../architecture/modules/transport_public.md), [visualisation](../architecture/modules/visualisation.md), [orchestration](../architecture/modules/orchestration.md)

## 1. Objectif
Voir sur la carte de `build_networks.ipynb`, pour chaque tronçon de bus : **le tracé GTFS initial**, **le tracé map-matché** et **pourquoi** il a réussi ou échoué. Ce plan **ne change pas le résultat** du map-matching : il le rend visible et mesurable, pour préparer sa correction (futur PLAN-003).

## 2. Décisions (validées le 2026-09-25 : propositions par défaut, D-2 = 2 couches)

| # | Décision | Proposition par défaut | Alternative |
|---|---|---|---|
| D-1 | Nom de la couche map-matchée (aujourd'hui « PT Lanes ») | **« PT bus map-matched »** | garder « PT Lanes » |
| D-2 | Affichage du GTFS initial | **2 couches** : « PT bus GTFS init - matched » (vert) et « PT bus GTFS init - not matched » (rouge) ; statut, longueur et écart de Hausdorff dans l'infobulle | 5 couches, une par statut d'échec (comme la carte de diagnostic d'AUDIT-002) |
| D-3 | Couche des liens OSM retenus (`final_matches`) | **oui** : « PT bus OSM links used » | non |
| D-4 | Sauvegarder le diagnostic avec le réseau | **oui** : nouvelle couche `pt_bus_routes_init` dans `network.gpkg` ; un réseau sauvegardé avant ce plan se charge toujours, simplement sans ces couches | non |

## 3. Diagnostic enregistré par tronçon

`MapMatchingPT2OSM` conserve, pour chaque tronçon GTFS de bus (après dédoublonnage), sa géométrie initiale et les colonnes :
`sub_route_id, route_id, line_name, status, n_candidates, n_links_path, len_init_m, len_matched_m, hausdorff_m`.
Valeurs de `status` : `no_candidate_link`, `no_start_or_end_link`, `no_path`, `path_too_short_dropped` (≤ 2 liens), `matched`.

## 4. Périmètre
- **Inclus** :
  - `build_network/build_pt_network/MatMatchingPT2OSM.py` : enregistrement du diagnostic, **sans changer** `final_matches` ni `final_pt_links` ;
  - `build_network/MultiModalNetwork.py` : exposer le diagnostic (`gtfs_network_builder.pt_bus_routes_init`), `save` / `load` ;
  - `plotting/PlottingMultimodal.py` : couches D-1 à D-3 ;
  - `README.md` : section « Map layers » ;
  - `tests/test_network_io.py` : chargement d'un réseau sans la nouvelle couche.
- **Exclu** : toute correction du map-matching ([OBS-21 — fragments](../audit/AUDIT-002_map_matching_bus.md), [OBS-22 — qualité](../audit/AUDIT-002_map_matching_bus.md), [OBS-24 — `final_matches` incohérent](../audit/AUDIT-002_map_matching_bus.md)), [OBS-03 — découpage sur le contour](../audit/AUDIT-001_exploration_initiale.md) et [OBS-23 — doublons par trip](../audit/AUDIT-002_map_matching_bus.md). Le notebook n'est pas modifié : la cellule de visualisation reste identique.
- **Données** : aucune écriture dans `data/`.

## 5. Étapes

| # | Étape | Fichiers | Agent | Fait |
|---|---|---|---|---|
| 1 | Diagnostic par tronçon dans `match_pt_to_osm` → attribut `bus_routes_diagnostics` (GeoDataFrame en 2154), construit par `_build_diagnostics` | `MatMatchingPT2OSM.py:25-101` | dev | [x] |
| 2 | `gtfs_network_builder.pt_bus_routes_init` ; couche `pt_bus_routes_init` dans `save` ; restaurée par `load` si présente | `MultiModalNetwork.py:104, 141, 246` | dev | [x] |
| 3 | Couches « PT bus GTFS init - matched / not matched », « PT bus map-matched », « PT bus OSM links used » | `PlottingMultimodal.py:133` (`_get_pt_bus_diagnostic_layers`) et `plotting()` | dev | [x] |
| 4 | Tests : réseau sans diagnostic → `pt_bus_routes_init is None` ; aller-retour du diagnostic | `tests/test_network_io.py` | dev | [x] |
| 5 | Bout en bout (voir §6) | scripts hors dépôt | dev | [x] |
| 6 | README (section « Map layers ») + fiches d'architecture | `README.md`, `markdown_claude/` | dev | [x] |
| 7 | Revue | — | auditeur | [x] (voir §10) |

## 6. Critères d'acceptation
- [x] **Non-régression** : l'algorithme a été rejoué avant et après modification sur les **mêmes entrées** (réseau de test de 3 IRIS sauvegardé) : `final_pt_links` (17) et `final_matches` (124) sont **identiques** (lignes, colonnes, géométries, index).
- [x] Le diagnostic retrouve la répartition d'[AUDIT-002](../audit/AUDIT-002_map_matching_bus.md) : 127 tronçons, dont 17 `matched`, 86 `path_too_short_dropped`, 15 `no_start_or_end_link`, 6 `no_candidate_link` et 3 `no_path` ; écart de Hausdorff médian 101,2 m, max 1 890,5 m.
- [x] La cellule de visualisation du notebook, non modifiée, affiche les 4 couches PT avec leurs infobulles (vérifié sur la nouvelle zone de l'utilisateur, 9 IRIS : 20 matched, 25 not matched, 179 liens OSM).
- [x] Même carte après `build()` et après `save()` → `load()` dans un processus neuf (22 couches Folium, mêmes effectifs).
- [x] Réseaux sauvegardés avant ce plan (réseau de test de PLAN-001 et réseau `trivial` de l'utilisateur, lu sans être modifié) : se chargent et s'affichent, sans les couches GTFS initiales.
- [x] `python tests/test_network_io.py` : 4/4 OK.

## 7. Risques / points d'attention
- Les réseaux sauvegardés avant PLAN-002 n'ont pas le diagnostic : il faut les reconstruire pour voir les couches GTFS initiales.
- `n_candidates` et `n_links_path` sont des `float` (valeurs manquantes pour `no_candidate_link`).

## 8. Découvertes en cours de route (hors périmètre, non traitées)
- **D-a** : `data.geojson` a été redessiné par l'utilisateur à 17:45 (9 IRIS). Le bout en bout a donc porté sur cette nouvelle zone ; la non-régression a été faite sur les entrées sauvegardées de l'ancienne zone.
- **D-b** : sur la nouvelle zone, 20 tronçons sur 45 sont map-matchés (44 %, contre 13 % sur l'ancienne). La fragmentation ([OBS-21](../audit/AUDIT-002_map_matching_bus.md)) dépend donc beaucoup de la forme de la zone.

## 9. Validation
- Proposé le : 2026-09-25
- **Validé par l'utilisateur le : 2026-09-25** (« OK PLAN-002 », propositions par défaut D-1 à D-4)
- Note : `draw_lane` ajoute toujours le suffixe « Lanes » au nom de couche ; la couche D-1 s'affiche donc « PT bus map-matched Lanes » (comme « Bike Lanes »).

## 10. Revue (auditeur)
- Réalisée le 2026-09-25 **dans la même session que le développement** : ce n'est pas une relecture indépendante.
- Diff : dans `MatMatchingPT2OSM.py`, uniquement des ajouts (le résultat renvoyé est inchangé, [OBS-24 — `final_matches` incohérent](../audit/AUDIT-002_map_matching_bus.md) volontairement conservé) ; dans `PlottingMultimodal.py`, seule suppression : l'ancien nom de couche `"PT"`. Fins de ligne CRLF homogènes. Aucune écriture dans `data/`.
- Résultat : **OK**. Statut : en attente de la confirmation de l'utilisateur (affichage dans son notebook), puis `TERMINE` et archivage.
