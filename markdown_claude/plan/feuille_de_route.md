---
role: plan (stratégique, commun à tous les agents)
lecteurs: tous les agents, utilisateur
maj: 2026-09-25
statut: PROPOSE
---

# Feuille de route (proposition, à valider)

Index : [plan/README.md](README.md) · Base : README du dépôt (« To do »), `Ignore/notes/reu_bahman.md`, [AUDIT-001](../audit/AUDIT-001_exploration_initiale.md) et les réponses de l'utilisateur (2026-09-25)

> Cette feuille de route **n'est pas validée**. Elle ordonne les chantiers ; chaque jalon donnera lieu à un ou plusieurs `PLAN-NNN` soumis séparément à validation.

## Vision

1. **Phase 1 : réseau multimodal** (en cours) : voiture, vélo, marche et TC dans un même réseau (routier sur OSM ; tram et métro en lignes propres), connexe, pour une zone choisie.
2. **Phase 2 : demande** : zonage (IRIS agrégés, grille, pavage), matrice OD a priori (ex. modèle gravitaire), affectation (utilitaires DUE dans `Ignore/`).
3. **Phase 3 : calibrage** : ajustement sur les boucles de comptage AVATAR (accès API à obtenir), publication des données (ex. figshare).

## Jalons proposés

| Jalon | Contenu | Constats / décisions liés | Statut |
|---|---|---|---|
| **J0 : sauvegarde / chargement** | `save` / `load` des réseaux ; jeux de test choisis par l'utilisateur via Streamlit puis sauvegardés | A-03, A-06 · [PLAN-001](../archive/plans/PLAN-001_sauvegarde_chargement_reseaux.md) | **terminé** (2026-09-25) |
| **J1 : map-matching des bus** (priorité utilisateur, 2026-09-25) | 1) rendre visible GTFS initial / map-matché / cause d'échec ; 2) corriger : map-matcher les lignes entières, découpage sur la surface, qualité, cohérence `final_matches` | [AUDIT-002](../audit/AUDIT-002_map_matching_bus.md) : OBS-21 fragments, OBS-22 qualité, OBS-23 doublons, OBS-24 incohérence ; [AUDIT-001](../audit/AUDIT-001_exploration_initiale.md) : OBS-03 découpage sur le contour · [PLAN-002](PLAN-002_affichage_diagnostic_map_matching.md) (affichage) puis PLAN-003 (correction) | **en cours** : PLAN-002 proposé |
| **J2 : robustesse** | cache GTFS au premier lancement, CRS selon la méthode de sélection de zone, complétion vitesses/capacités, erreurs OSM, sortie Streamlit, configuration | [AUDIT-001](../audit/AUDIT-001_exploration_initiale.md) : OBS-02, 04, 05, 06, 07, 08, 16 | |
| **J3 : multimodal réel** | tram/métro/funiculaire en **lignes propres indépendantes d'OSM** (géométrie GTFS + arrêts + connecteurs) ; bus map-matchés sur OSM ; intégration du vélo ; connecteurs intermodaux ; connexité / plus grande composante ; choix des modes | OBS-10, 20, A-04, Q-01 | |
| **J4 : nettoyage** | pycache, sorties de notebooks, artefacts suivis, fichier d'environnement, factorisation, sort du legacy, API dépréciées | OBS-09, 12-15, 17, 18, 19, Q-07 bis | **reporté** (A-05) |
| **J5 : phase 2** | centroïdes et connecteurs de zones, OD a priori, affectation | — | |

Les tests reposent sur les réseaux sauvegardés en J0 (A-06) : pas de jeu de test séparé à construire.

## Ouvert

- Q-02 (fond) : union des IRIS ou polygone exact. Le comportement actuel est désormais documenté dans le README racine.
- Hypothèses de `utils/network.py` à revoir (README) : il faut une source de référence (à fournir par l'utilisateur).
