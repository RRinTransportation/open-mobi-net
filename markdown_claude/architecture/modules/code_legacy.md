---
role: architecture
lecteurs: agents qui envisagent un nettoyage ou cherchent une ancienne implémentation
maj: 2026-09-25
---

# Code legacy, exploratoire ou non branché

Retour : [vue_ensemble](../vue_ensemble.md) · Dépendances : [graphe_dependances](../graphe_dependances.md)

> Rien ici ne doit être supprimé sans plan validé : certains fichiers contiennent des idées réutilisables.

| Élément | Nature | Relation avec le pipeline actif | Idées réutilisables |
|---|---|---|---|
| [load_network/car.py](../../../load_network/car.py) | chargement réseau depuis `aequilibrae_lyon6/*.csv` | remplacé par `AequilibraeBuilder` | appelle `add_speed_when_missing` (absent de l'actif, OBS-04) ; séparation car / anomalies (buggée, OBS-14) ; lecture des nœuds GMNS (`x_coord, y_coord`) |
| [load_network/bike.py](../../../load_network/bike.py) | vélo depuis OSM ou SHP prétraité | remplacé | voies cyclables par sens (`cycleway_left/right`), exclusion > 50 km/h, **CRS 2154 correct** pour le SHP (cf. OBS-01) |
| [load_network/area.py](../../../load_network/area.py) | zone d'étude par filtre `NOM_COM` | remplacé par `NetworkBuilder` | — (`unary_union` déprécié) |
| [load_network/pt.py](../../../load_network/pt.py) | version fonctionnelle du map-matching | remplacé par `MapMatchingPT2OSM` (copie quasi identique) ; import mort | reprojette ses sorties en 4326 (la classe ne le fait pas) |
| [utils/conversion_gtfs.py](../../../utils/conversion_gtfs.py) (605 lignes) | script « WORK IN PROGRESS » GTFS → graphe **MnMS** (tram/métro/bus, map-matching arrêt par arrêt au plus proche lien, `mapmatch_dist=50`) | aucun ; copie dans `data/.../net_pt/GTFS/` | piste pour projeter tram/métro (OBS-10) et pour un export vers un simulateur |
| ~~`anomalies.ipynb`~~ — **supprimé par l'utilisateur** (2026-09-25, non commité) | ancienne copie du notebook principal + exploration des anomalies voiture | son contenu est désormais intégré à `build_networks.ipynb` (couche « Car anomalies ») | — |
| `Ignore/build_networks_old.ipynb`, `Ignore/load_networks.ipynb` | anciens notebooks (map-matching pas à pas, requêtes SQL transit) | ignorés par git | débogage de lignes précises (ex. ligne 38, route 10051000000) |
| `Ignore/notebooks/utils_aeq_due.py` (696 lignes) | grille synthétique, lecture OD/réseau, **affectation DUE AequilibraE** | ignoré | **base probable de la phase 2** (demande + affectation) |
| `Ignore/notes/reu_bahman.md` | notes de réunion : feuille de route | ignoré | reprise dans [feuille_de_route](../../plan/feuille_de_route.md) |
| `data/.../net_bike/net_bike.py` | script de prétraitement vélo (non lu en détail) | hors dépôt git | origine de `links_processed.shp` — à consulter pour OBS-01 |
| `__init__.py` (racine) | contient `# Init` | fait de la racine un paquet | — |
| `selected_area.geojson` (racine) | ancien polygone | non utilisé | — |
