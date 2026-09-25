---
role: audit
lecteurs: utilisateur (synthèse), auditeur, dev
maj: 2026-09-25
statut: A_REVOIR
---

# AUDIT-002 — Map-matching des bus (GTFS → OSM)

Index : [audit/README.md](README.md) · Fiche module : [transport_public.md](../architecture/modules/transport_public.md) · Audit précédent : [AUDIT-001](AUDIT-001_exploration_initiale.md)

**Demande** (2026-09-25) : l'utilisateur veut reprendre le problème du map-matching des bus, et voir sur la carte le tracé GTFS initial à côté du tracé map-matché.
**Méthode** : l'algorithme existant (`MapMatchingPT2OSM`, mêmes méthodes, mêmes paramètres) est rejoué **hors dépôt** sur le réseau de test sauvegardé (zone de `data.geojson`, 3 IRIS, 11 lignes de bus), en notant le sort de chaque tronçon. **Aucune modification du code.**

---

## Synthèse

1. **Ce que montre la carte actuelle** : la couche « PT Lanes » est **uniquement le résultat map-matché** (`final_pt_links` : tracés recomposés à partir de liens OSM). Le tracé GTFS initial n'est affiché nulle part, pas plus que les liens OSM retenus (`final_matches`). Comme toutes les couches, « PT Lanes » est masquée par défaut.
2. **Le map-matching échoue pour 110 tronçons sur 127** (87 %) : les lignes sont découpées par la zone d'étude **avant** d'être projetées, en fragments très courts (médiane **16 m**), traités un par un (**OBS-21**, détaillé plus bas).
3. **Les 17 tracés réussis sont eux-mêmes éloignés du GTFS** : écart de Hausdorff médian **101 m**, maximum **1,9 km**, aucun sous 20 m (**OBS-22**, détaillé plus bas).
4. Les **arrêts** sont tous perdus (23 dans la zone, 0 retenu), ce qui confirme [OBS-03 — découpage TC sur le contour du polygone](AUDIT-001_exploration_initiale.md).

Carte de diagnostic (provisoire, générée hors dépôt) : tracés GTFS colorés selon leur sort, tracés map-matchés en pointillés bleus, liens OSM utilisés. Voir « Fichiers de diagnostic » en fin de document.

---

## Chiffres (zone de test, 2026-09-25)

| Étape | Valeur |
|---|---|
| Lignes `pt_links_inside` | 4 072 (tout en bus ; **une ligne par trip**, soit 11 à 166 trips par ligne) |
| Tronçons distincts après dédoublonnage | **127** pour 11 lignes |
| Longueur des tronçons | médiane **16 m** ; 10 % < 3 m ; 90 % < 1 151 m ; **65 % < 50 m** |
| Sort des 127 tronçons | 6 sans lien candidat · 15 sans lien de départ ou d'arrivée · 3 sans chemin · **86 chemin de ≤ 2 liens → écartés** · **17 map-matchés** |
| Qualité des 17 tracés map-matchés | Hausdorff GTFS ↔ OSM : médiane 101 m, max 1 890 m ; longueur OSM / GTFS : médiane 0,88 (de 0,35 à 0,97) |
| Arrêts dans la zone / retenus | 23 / **0** |

---

## Constats

### OBS-21 — Le map-matching traite des fragments de lignes, pas des lignes · Haute · C + exécution
- **Où** : découpage par [GTFSNetworkBuilder.restrain_to_area_study](../../build_network/build_pt_network/GTFSNetworkBuilder.py#L22-L31) (`intersection` avec le polygone puis `explode`) ; boucle par fragment et filtre `len(best_path) > 2` dans [MatMatchingPT2OSM.match_pt_to_osm](../../build_network/build_pt_network/MatMatchingPT2OSM.py#L47-L72).
- **Constat** : la zone d'étude est l'union d'IRIS, dont les limites suivent souvent des rues. Une ligne de bus qui emprunte une rue-frontière est coupée en dizaines de morceaux : une ligne produit **72 fragments** (9 une fois recollés). Chaque fragment est map-matché seul, et ceux qui tiennent sur 1 ou 2 liens OSM sont écartés.
- **Effet** : 87 % des tronçons ne donnent aucun tracé ; les lignes affichées sont trouées.

### OBS-22 — Les tracés map-matchés s'éloignent du tracé GTFS · Haute · exécution (causes : V)
- **Constat** : pour les 17 réussites, l'écart maximal entre le tracé GTFS et le tracé OSM est de 101 m en médiane et atteint 1,9 km ; aucun n'est sous 20 m.
- **Causes probables, à vérifier** :
  - graphe **non orienté** (`nx.from_pandas_edgelist` → `nx.Graph`) : sens de circulation ignoré, et deux liens entre les mêmes nœuds sont fusionnés ;
  - liens de départ et d'arrivée pris dans un rayon de 10 m autour des extrémités, qui inclut les rues transversales ; le meilleur chemin parmi **toutes** les paires départ/arrivée peut aller d'un point à un autre sans suivre la ligne ;
  - coût `Hausdorff² + |Δlongueur| + 1` calculé par lien sur une projection du tracé, instable pour les fragments courts ;
  - types de liens exclus (`living_street`, `path`…) qui peuvent retirer des rues réellement empruntées.

### OBS-23 — Tracés GTFS dupliqués par trip · Moyenne · C
- `pt_links_inside` contient une ligne **par trip** (4 072 lignes pour 127 géométries distinctes). Le dédoublonnage n'a lieu que dans le map-matching : alourdit la mémoire et la sauvegarde. Origine : requête `sql_links_query` (jointure `trips` ⋈ `routes`) de [SQL_query.py](../../build_network/build_pt_network/SQL_query.py).

### OBS-24 — `final_matches` incohérent avec `final_pt_links` · Basse · C
- [MatMatchingPT2OSM.py:72](../../build_network/build_pt_network/MatMatchingPT2OSM.py#L72) : `final_link_indices.extend(best_path)` est **hors** du `if len(best_path) > 2`. Les liens OSM des chemins écartés figurent donc dans `final_matches` alors que le tracé correspondant n'est pas dans `final_pt_links`.

### Complément à OBS-03 (voir [AUDIT-001](AUDIT-001_exploration_initiale.md))
- 23 arrêts sont dans la zone, 0 est retenu. Sur cette petite zone, les 11 lignes traversent toutes la frontière, donc aucune ligne entière n'est perdue ; sur une zone plus grande, les lignes entièrement intérieures le seraient.

---

## Questions ouvertes pour l'utilisateur

- **Q-08** — Les tracés de `net_pt/lines/lines.shp` sont probablement **déjà recalés par AequilibraE** (`transit.map_match()` dans [GTFSImporter](../../build_network/build_pt_network/GTFSImporter.py#L49-L51)), mais sur un autre téléchargement OSM. Le map-matching maison refait donc ce travail avec d'autres identifiants de liens. À terme, préférez-vous : (a) améliorer le map-matching maison ; (b) réutiliser celui d'AequilibraE sur le même réseau OSM ; (c) repartir des arrêts GTFS ? *(Point à vérifier d'abord ; il n'est pas nécessaire de trancher pour PLAN-002.)*
- **Q-09** — Pour la correction : map-matcher chaque **ligne entière**, puis la découper par la zone (au lieu de découper puis map-matcher) vous convient-il ? *(Ce serait le cœur d'un futur PLAN-003.)*

## Fichiers de diagnostic (hors dépôt, provisoires)
Dans le dossier temporaire de la session Claude : `diag_mapmatching.html` (carte), `diag_mapmatching.csv` (un tronçon par ligne : statut, nombre de candidats, longueur, Hausdorff) et `diag_mapmatching.py` (script). Ils ne sont pas conservés ; PLAN-002 intègre l'équivalent dans le code.
