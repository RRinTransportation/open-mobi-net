---
role: tableau de bord
lecteurs: tous les agents (à lire à chaque session, à mettre à jour en fin de session)
maj: 2026-09-25
---

# ÉTAT COURANT

> Fichier court, uniquement le vivant. Chaque identifiant renvoie au markdown qui le définit ([conventions](gouvernance/conventions.md)). Historique : [archive/JOURNAL.md](archive/JOURNAL.md).

## Phase actuelle

**Jalon J1 — map-matching des bus** ([feuille de route](plan/feuille_de_route.md)) : diagnostic fait ([AUDIT-002](audit/AUDIT-002_map_matching_bus.md)) ; affichage GTFS initial / map-matché **réalisé** ([PLAN-002](plan/PLAN-002_affichage_diagnostic_map_matching.md), revue OK), en attente de votre confirmation.
Aucun autre plan n'est validé → aucune autre modification de code n'est autorisée.

## Livrables ouverts

| Livrable | Sujet | Statut |
|---|---|---|
| [PLAN-002](plan/PLAN-002_affichage_diagnostic_map_matching.md) | Afficher le GTFS initial, le tracé map-matché et la cause d'échec de chaque tronçon de bus | `EN_COURS` : réalisé, revue OK, confirmation attendue |
| [AUDIT-002](audit/AUDIT-002_map_matching_bus.md) | Diagnostic chiffré du map-matching des bus | `A_REVOIR` |
| [AUDIT-001](audit/AUDIT-001_exploration_initiale.md) | Audit initial du dépôt | `A_REVOIR` : 2 questions non urgentes |
| [Feuille de route](plan/feuille_de_route.md) | Ordre des chantiers (jalons J0 à J5) | `PROPOSE` |

Terminé : [PLAN-001 — sauvegarde / chargement des réseaux](archive/plans/PLAN-001_sauvegarde_chargement_reseaux.md) (2026-09-25).

## Décisions attendues de l'utilisateur

Référence : [PLAN-002](plan/PLAN-002_affichage_diagnostic_map_matching.md) §2 et [AUDIT-002](audit/AUDIT-002_map_matching_bus.md) « Questions ».

1. **Clore PLAN-002** : vérifier dans votre notebook les couches « PT bus … » (réseau à reconstruire : `trivial` a été sauvegardé avant PLAN-002).
2. **Q-09** (AUDIT-002) : pour la future correction (PLAN-003), map-matcher chaque ligne **entière** puis la découper par la zone ?
3. **Q-08** (AUDIT-002), non urgente : garder un map-matching maison ou réutiliser celui d'AequilibraE ?
4. Non urgentes ([AUDIT-001](audit/AUDIT-001_exploration_initiale.md)) :
   - Q-02 : zone d'étude = union des IRIS ou polygone exact ;
   - Q-07 bis : que faire des anciens fichiers de `load_network/`.

## Prochaine action attendue d'un agent

À la confirmation : archiver [PLAN-002](plan/PLAN-002_affichage_diagnostic_map_matching.md). Ensuite : rédiger PLAN-003 (correction du map-matching), selon la réponse à Q-09 d'[AUDIT-002](audit/AUDIT-002_map_matching_bus.md).

## Contexte technique à garder en tête

- **Utilisateur** : il travaille uniquement en Python et dans des notebooks, pas avec QGIS. Contrôles visuels : carte Folium du notebook.
- **Réseaux de test** : ancienne zone de 3 IRIS (chiffres de référence dans [AUDIT-002](audit/AUDIT-002_map_matching_bus.md)) ; `data.geojson` a été redessiné le 2026-09-25 à 17:45 (9 IRIS : 20 tronçons de bus map-matchés sur 45). Réseau sauvegardé par l'utilisateur : `data/Lyon/ready_input/networks/trivial` (sans diagnostic).
- **Modifications non commitées** : celles de l'utilisateur (dont la suppression de `anomalies.ipynb`, intégré à `build_networks.ipynb`) et celles de [PLAN-001](archive/plans/PLAN-001_sauvegarde_chargement_reseaux.md) et [PLAN-002](plan/PLAN-002_affichage_diagnostic_map_matching.md) (`build_network/build_pt_network/MatMatchingPT2OSM.py`, `build_network/MultiModalNetwork.py`, `build_network/network_io.py`, `config/Lyon_multimodal.py`, `plotting/PlottingMultimodal.py`, `build_networks.ipynb`, `README.md`, `tests/`). Rien n'a été commité.
- **Fichier compilé suivi par git** : `build_network/__pycache__/MultiModalNetwork.cpython-312.pyc` est réécrit à chaque import, de même que `load_network/__pycache__/pt.cpython-312.pyc` ([OBS-18 — hygiène du dépôt](audit/AUDIT-001_exploration_initiale.md), nettoyage reporté).
- **Python** : env micromamba `aequilibrae` (`C:/Users/r.rochas/micromamba/envs/aequilibrae/python.exe`). Pas de `pytest` : lancer `python tests/test_network_io.py`.
