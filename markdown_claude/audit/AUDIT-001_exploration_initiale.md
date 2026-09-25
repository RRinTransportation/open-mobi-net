---
role: audit
lecteurs: utilisateur (synthèse), auditeur, dev
maj: 2026-09-25
statut: A_REVOIR
---

# AUDIT-001 — Exploration initiale du dépôt

Index : [audit/README.md](README.md) · Architecture : [vue_ensemble](../architecture/vue_ensemble.md)

**Méthode** : lecture intégrale des 2 815 lignes Python, des cellules des notebooks, du diff non commité et de l'arborescence `data/` ; vérification des emprises des shapefiles (en-têtes binaires) et du comportement de Folium dans l'env `aequilibrae`. **Aucune exécution du pipeline** (réseau, Streamlit et durée) → les constats marqués *à vérifier* demandent une exécution.
**Aucune modification n'a été faite.**

> **Suivi 2026-09-25** : réponses de l'utilisateur reçues (Q-01 à Q-07, en fin de fichier) avec un retour de l'auditeur sous chacune. En suspens : Q-01 (après la vérification d'OBS-01), Q-02 (question de fond), Q-07 bis.

Niveaux de confiance : **C** = constaté dans le code · **P** = probable (déduit) · **V** = à vérifier par exécution.

---

## Synthèse (à lire en priorité)

1. **Le pipeline fonctionne aujourd'hui grâce à des caches présents sur le disque**, pas par construction : un premier lancement (nouvelle ville ou cache GTFS supprimé) échouerait (OBS-02), et seule la sélection **par polygone dessiné** produit des CRS cohérents (OBS-06).
2. **Deux défauts donnent probablement des résultats silencieusement faux** : le réseau vélo prétraité est lu avec le mauvais CRS (OBS-01) et le découpage TC joint sur le **contour** du polygone, pas sur sa surface (OBS-03).
3. **Écart avec l'objectif du README** : les modes ne sont pas encore reliés en un graphe unique. Seuls les bus sont projetés sur OSM ; vélo SHP, tram et métro ne le sont pas ; il n'y a pas de connecteurs intermodaux (OBS-10, OBS-20).
4. **Dette technique modérée et localisée** : duplication legacy/actif, hypothèses de capacité incomplètes (OBS-04/05), dépôt alourdi (notebooks de 38 Mo, pycache suivi) et absence de fichier d'environnement et de tests (OBS-18).

Priorités suggérées (à valider) : **OBS-01, 02, 03, 06** (justesse) → **OBS-04, 05, 07, 08** (robustesse) → **OBS-18** (hygiène) → **OBS-10, 20** (évolution, feuille de route).

---

## Constats détaillés

### OBS-01 — Vélo : shapefile Lambert-93 déclaré en EPSG:4326 · Haute · C + vérifié par exécution (voir retour sous A-01)
- **Où** : [MultiModalNetwork.py:85-90](../../build_network/MultiModalNetwork.py#L85-L90) (`init_crs='EPSG:4326'`) → [AequilibraeBuilder.add_bike_network](../../build_network/AequilibraeBuilder.py#L66) → `load_init_area` qui **force** `gdf.crs = init_crs`.
- **Constat** : `links_processed.shp` n'a pas de `.prj` et son emprise est (832 473 ; 6 509 932) – (852 964 ; 6 528 970), donc du Lambert-93. L'ancien code ([load_network/bike.py:36](../../load_network/bike.py#L36)) le lisait en 2154.
- **Effet probable** : `.clip(study_area_polygon)` compare des mètres à des degrés → `bike_lanes`/`bike_nodes` vides. Sans conséquence visible aujourd'hui car ces attributs ne sont pas utilisés (OBS-20).

### OBS-02 — GTFSImporter : le premier lancement ne produit pas le cache · Haute · C
- **Où** : [MultiModalNetwork.py:112-119](../../build_network/MultiModalNetwork.py#L112-L119), [GTFSImporter.py:28-29, 57-62, 91-94](../../build_network/build_pt_network/GTFSImporter.py#L28).
- **Constat** : le constructeur n'appelle que `_start()` et `_load_gtfs_route()` ; `_SQL_extract()` (qui écrit les SHP) n'est jamais appelée. `_save_shapefiles` utilise `self.gtfs_folder_name`, qui n'existe pas, et viserait `net_pt/GTFS/<?>/stops` alors que la lecture se fait dans `net_pt/stops`. `GTFSImporter` refait aussi un téléchargement OSM complet.
- **Effet** : sans `net_pt/stops/stops.shp` préexistant, ~1 h de calcul puis échec de `GTFSNetworkBuilder` (fichier introuvable).

### OBS-03 — Découpage TC joint sur le contour du polygone · Haute · C (effet : V)
- **Où** : [GTFSNetworkBuilder.py:17-20](../../build_network/build_pt_network/GTFSNetworkBuilder.py#L17-L20) (idem [load_network/pt.py:19](../../load_network/pt.py#L19)).
- **Constat** : `sjoin(..., predicate='intersects')` avec `study_area_polygon.exterior` (une ligne) : seuls les tracés qui **traversent la frontière** sont retenus ; les arrêts retenus sont ceux situés **sur** la frontière. `.exterior` n'existe pas pour un `MultiPolygon` (IRIS non contigus).
- **Effet probable** : lignes entièrement intérieures absentes, `pt_nodes_inside` quasi vide, crash si la zone d'étude est multi-parties.
- **Confirmé par exécution (2026-09-25, PLAN-001)** : sur la zone de `data.geojson`, `pt_nodes_inside` = **0 arrêt** ; `pt_links_inside` = 4 072 tronçons, tous issus de tracés qui traversent la frontière.

### OBS-04 — Vitesses manquantes non complétées dans le pipeline actif · Moyenne · C
- **Où** : [AequilibraeBuilder.preprocess_network](../../build_network/AequilibraeBuilder.py#L55-L62).
- **Constat** : n'appelle que `add_lanes_when_missing` et `add_capacity_on_car_links` (les deux sur `self.links`, modifié en place : le résultat de la première affectation est écrasé, lecture trompeuse). `add_speed_when_missing` n'est appelée que par le legacy [car.py:49](../../load_network/car.py#L49).
- **Effet** : liens à vitesse manquante → capacité `None`, alors qu'une hypothèse de vitesse existe dans `utils/network.py`.

### OBS-05 — `estimate_capacity` : KeyError hors table · Moyenne · C (fréquence : V)
- **Où** : [utils/network.py:146-149](../../utils/network.py#L146-L149).
- **Constat** : si `link_type` ∉ `LANE_CAPACITY_ASSUMPTIONS`, la vitesse doit être une clé **exacte** de `CAPACITY_ASSUMPTIONS_BASED_ON_SPEED` (10, 15, 20, 30, 50…). Une vitesse OSM de 5, 25 ou 45 km/h sur un `service` ou un `living_street` lève `KeyError`. L'ajout récent (non commité) de la clé `10.0` suggère que le cas a déjà été rencontré.

### OBS-06 — CRS incohérents selon la méthode de sélection de zone · Moyenne · C
- **Où** : [builder.py:71-86, 124-130](../../build_network/builder.py#L71), [MultiModalNetwork.py:135-137](../../build_network/MultiModalNetwork.py#L135-L137).
- **Constat** : `run()` charge les IRIS en 2154 sans reprojeter ; seule `_select_from_polygon` repasse en 4326. Avec `selection_from_polygon=False` (filtre attributaire ou SHP), `study_area_polygon` est en mètres mais utilisé comme 4326 (OSM, GTFS, `_build_zones`). `_restrict_to_study_area` écrase le CRS du SHP de restriction par `init_crs`, puis compare un polygone 4326 à des IRIS éventuellement en 2154.
- **Effet** : seules les combinaisons incluant le polygone dessiné fonctionnent.

### OBS-07 — Sélection Streamlit : attente infinie, dépendance au cwd · Moyenne · C
- **Où** : [builder.py:102-114](../../build_network/builder.py#L102-L114).
- **Constat** : `process.poll()` n'est testé qu'une fois, juste après `Popen` ; si l'utilisateur ferme la fenêtre sans sauvegarder, la boucle `while not os.path.exists` ne se termine jamais. Le chemin du script, `data.geojson` et `data/...` sont relatifs au dossier courant. Le chemin d'export saisi dans l'UI n'est pas pris en compte par le parent.

### OBS-08 — Erreurs OSM avalées, double téléchargement · Moyenne · C
- **Où** : [AequilibraeBuilder.py:32-38](../../build_network/AequilibraeBuilder.py#L32-L38), [GTFSImporter.py:33-36](../../build_network/build_pt_network/GTFSImporter.py#L33-L36).
- **Constat** : l'exception de `create_from_osm` est affichée puis ignorée ; l'erreur réelle survient plus loin, sous une forme moins lisible. Les projets temporaires `%TEMP%/<uuid>` ne sont jamais supprimés. `_save_project` utilise `os.mkdir` (pas de création des parents).

### OBS-09 — Héritage artificiel `AequilibraeBuilder(NetworkBuilder)` · Basse · C
- `super().__init__()` sans arguments → `self.target_crs`, `self.IRIS_folder_path`… prennent les **valeurs par défaut**, pas celles de la config (le `target_crs` utilisé pour le vélo n'est donc pas le configuré). Aucune méthode héritée n'est utilisée. Imports inutilisés (`matplotlib`, `math`, `uuid`…) dans `builder.py` et `AequilibraeBuilder.py`.

### OBS-10 — Map-matching limité aux bus · Moyenne · C
- **Où** : [MatMatchingPT2OSM.py:29, 66](../../build_network/build_pt_network/MatMatchingPT2OSM.py#L29).
- Tram, métro et funiculaire sont ignorés ; les chemins de 2 liens ou moins sont écartés ; le graphe est non orienté (sens de circulation ignoré) ; les sorties restent en 2154. Correspond au « To do » du README.

### OBS-11 — Agrégation IRIS : `assert` fragile · Basse · P/V
- **Où** : [load_network/iris.py:55](../../load_network/iris.py#L55).
- L'`assert` suppose que les deux plus petits scores forment une paire réciproque. Il échoue si des zones restent sans voisin (`inf - inf = nan`, par exemple avec une sélection d'IRIS non contigus) ou en cas d'égalité entre paires distinctes. `within=True` sur un cordon égal à l'union des mêmes IRIS peut, par imprécision numérique, exclure des zones (V).

### OBS-12 — `add_network_layer(draw_arrows=False)` plante · Basse · C
- [plotting_folium.py:153](../../plotting/plotting_folium.py#L153) : `layer_group_arrows.add_to(...)` est hors du `if draw_arrows` → `NameError`. Cas non déclenché aujourd'hui (valeur par défaut `True`).

### OBS-13 — Filtre « Walk Only » ambigu · Basse · C (intention à confirmer)
- [PlottingMultimodal.py:71](../../plotting/PlottingMultimodal.py#L71) : `(w & pedestrian) | footway` ; l'intention est peut-être `w & (pedestrian | footway)`.

### OBS-14 — Bugs dans le legacy · Basse · C
- [load_network/car.py:65-66](../../load_network/car.py#L65-L66) : `car_links_anomalies` est calculé **après** filtrage → toujours vide. [load_network/iris.py:12](../../load_network/iris.py#L12) : `Iris_lyon.shp` au lieu de `Iris_Lyon.shp` (casse sensible hors Windows). `MultiModalNetwork.__main__` ne passe pas les arguments obligatoires `plane_projection` et `target_n_zones`.

### OBS-15 — Duplication et code mort (map-matching) · Basse · C
- `load_network/pt.py` ≈ `MatMatchingPT2OSM` + `GTFSNetworkBuilder.restrain_to_area_study`. Import inutilisé `get_candidates_links`. `_find_possible_extremities` et `find_best_path_for_route` (force brute avec `print`) ne sont pas utilisés. Le filtre réseau voiture est dupliqué à 3 endroits ([reseau_routier](../architecture/modules/reseau_routier.md)).

### OBS-16 — Configuration · Basse · C
- [config/Lyon_multimodal.py](../../config/Lyon_multimodal.py) : `parse_args(args=[])` rend la CLI inopérante ; `type=bool` (toute chaîne non vide vaut `True`) et `type=list` (découpe en caractères) sont des pièges si la CLI est réactivée ; `save_path` absent → zones agrégées jamais sauvegardées ; `city` inutilisé ; de nombreux paramètres sont codés en dur ([config.md](../architecture/modules/config.md)).

### OBS-17 — API dépréciée · Info · C
- `GeoSeries.unary_union` ([PlottingMultimodal.py:32](../../plotting/PlottingMultimodal.py#L32), [area.py:13](../../load_network/area.py#L13)) → `union_all()` (geopandas ≥ 1.0).

### OBS-18 — Hygiène du dépôt · Moyenne · C
- `__pycache__/*.pyc` suivis par git (cpython-312) et `.pyc` cpython-314 non suivis ; `.gitignore` sans `__pycache__`.
- Notebooks versionnés avec leurs sorties : `anomalies.ipynb` 38 Mo, `build_networks.ipynb` 4,7 Mo.
- Artefacts d'exécution suivis : `data.geojson` (réécrit à chaque run), `selected_area.geojson`.
- Pas de `requirements.txt` / `environment.yml` (shapely, pandas, tqdm, xyzservices non listés) ; pas de tests ; le README cite `build_network.ipynb` (le fichier réel est `build_networks.ipynb`).

### OBS-19 — `utils/conversion_gtfs.py` non branché · Info · C
- Script autonome vers MnMS, marqué « WORK IN PROGRESS », dupliqué dans `data/.../GTFS/` ; dépendances non déclarées (`mnms`, `gtfs_functions`, `coordinates`, `unidecode`). Importer `utils/` ne l'exécute pas (garde `__main__`), mais un `import utils.conversion_gtfs` échouerait sans ces paquets.

### OBS-20 — Écart avec l'objectif « multimodal sur un même graphe OSM » · Haute (objectif) · C
- Vélo SHP chargé mais ni utilisé ni rattaché à OSM ; marche = OSM brut ; TC = bus seulement, sous forme de liste de `link_id` OSM (pas de nœuds d'arrêt insérés dans le graphe, pas d'horaires) ; aucun connecteur intermodal ni contrôle de connexité (plus grande composante connexe, besoin cité dans les notes de réunion).

---

## Questions ouvertes pour l'utilisateur

- **Q-01** — Confirmez-vous que `net_bike/shapes/*_processed.shp` sont en Lambert-93 ? Ce réseau vélo doit-il compléter/remplacer le vélo OSM, ou être abandonné ?
  - **A-01**: le réseau vélo est effectivement disponible en Lambert-94, mais ceci ne pose pas de problème car la function `load_network_from_preprocessed` dans load_network/bike.py appelle la fonction `load_shp_from_2154` de `utils/network.py` qui converti en EPSG:4326.
  - ↳ **Retour auditeur (2026-09-25)** : `load_network_from_preprocessed` gère correctement le CRS, mais **elle n'est appelée nulle part dans le pipeline actif** (seulement dans `Ignore/load_networks.ipynb`). Le notebook passe par `MultiModalNetwork._build_traffic_network` → `AequilibraeBuilder.add_bike_network(init_crs='EPSG:4326')` → `load_init_area`, qui **force** le CRS 4326 sans reprojeter. **Vérifié par exécution** (lecture seule) sur la zone actuelle (`data.geojson`, 3 IRIS) : le pipeline actif garde **0** lien vélo après découpage, contre **1 234** si le fichier est lu en 2154. → OBS-01 passe à `CONFIRME`. Correctif d'une ligne possible (`init_crs='EPSG:2154'`), proposé en option dans [PLAN-001](../archive/plans/PLAN-001_sauvegarde_chargement_reseaux.md). *(Précision : EPSG:2154 correspond au Lambert-93.)*
- **Q-02** — La zone d'étude doit-elle être **l'union des IRIS intersectés** (comportement actuel, plus large) ou **le polygone dessiné exact** ?
  - C'est une question ouverte. Actuellement je crois que c'est l'union des IRIS intersectés, si ce n'est pas notifié dans le README.md à la racine du repo, il faut le notifier de façon simple, claire, et concise.
  - ↳ **Retour auditeur** : confirmé dans le code ([builder.py:44](../../build_network/builder.py#L44) garde les IRIS qui *intersectent* le polygone, puis [builder.py:86](../../build_network/builder.py#L86) en fait l'union). Ce n'était pas indiqué dans le README : **une phrase a été ajoutée** dans la section « Good to know » du README racine (à votre demande). La question de fond (union ou polygone exact) reste ouverte.
- **Q-03** — Priorité : fiabiliser le pipeline actuel (OBS-01…08) avant d'avancer sur la phase 2 (OD / calibrage) ?
  - Avant tout ça, la priorité numéro 1 sera d'enregistrer des network, et qu'ils puissent être load facilement en ajoutant un argument ou en rajoutant une fonction. Par exemple "multi_modal_network.load(path)" en mettant le path d'un réseau qu'on aura crée et sauvegardé au paravant avec multi_modal_network.build(). Il faut alors crée aussi une sauvegarde.
  - ↳ **Retour auditeur** : devient [PLAN-001](../archive/plans/PLAN-001_sauvegarde_chargement_reseaux.md) (statut `PROPOSE`). Attention : un réseau sauvegardé avant les corrections de OBS-01 (vélo vide) et OBS-03 (découpage TC) contiendra ces défauts ; les métadonnées de sauvegarde permettront de repérer les réseaux à reconstruire.
- **Q-04** — Tram / métro : les projeter sur OSM (voies ferrées) ou les garder comme lignes propres reliées aux arrêts par des connecteurs ?
  - Il faudra faire des lignes propres, car elle sont indépendantes de OSM. 
  - ↳ **Retour auditeur** : OBS-10 est recadré. Limiter le map-matching aux bus est **voulu** ; le manque réel est que tram, métro et funiculaire ne sont pas encore construits comme lignes propres (géométrie GTFS, arrêts, connecteurs). Reporté au jalon J3 de la [feuille de route](../plan/feuille_de_route.md).
- **Q-05** — Un nettoyage du dépôt (pycache, sorties de notebooks, artefacts suivis, fichier d'environnement) peut-il faire l'objet d'un plan ?
  - ça peut, mais plus tard, pas nécessaire pour le moment.
  - ↳ **Retour auditeur** : OBS-18 passe à `REPORTE`.
- **Q-06** — Souhaitez-vous un jeu de test minimal hors ligne (petite zone figée : extrait OSM + GTFS) pour valider chaque modification sans Streamlit ni téléchargement ?
  - ça rejoint la réponse à la Q-03. Et je m'occuperait de choisir un pour plusieurs jeu de test minimal depuis streamlit une fois les réseaux sauvegardé
  - ↳ **Retour auditeur** : pris en compte dans PLAN-001. La sauvegarde conserve aussi le polygone dessiné et les paramètres, pour que chaque jeu de test puisse être rechargé hors ligne et reconstruit à l'identique.
- **Q-07** — Code legacy (`load_network/{car,bike,area,pt}.py`) : le conserver tel quel, le déplacer (par ex. dans `Ignore/`) ou le supprimer après avoir récupéré les idées utiles ?
  - Pas compris.
  - ↳ **Reformulation (Q-07 bis)** : le dossier `load_network/` contient 5 fichiers. Un seul, `iris.py`, sert encore au pipeline. Les 4 autres (`car.py`, `bike.py`, `area.py`, `pt.py`) sont d'**anciennes versions** du code : le notebook `build_networks.ipynb` ne les appelle plus, car leur travail est désormais fait par `NetworkBuilder`, `AequilibraeBuilder` et `MapMatchingPT2OSM`. Ils restent dans le dépôt et peuvent induire en erreur : votre réponse A-01 s'appuyait justement sur l'un d'eux. Que souhaitez-vous en faire ?
    1. **Les laisser tels quels** (aucun changement) ;
    2. **Les déplacer** dans un dossier explicite (par ex. `legacy/`) pour signaler qu'ils ne sont plus utilisés ;
    3. **Les supprimer** : ils restent consultables dans l'historique git.

    Rien ne presse : cela relève du nettoyage (jalon J4), que vous avez reporté.
