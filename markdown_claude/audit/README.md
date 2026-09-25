---
role: audit
lecteurs: auditeur, dev (pour retrouver un constat par son ID), utilisateur
maj: 2026-09-25
---

# Audits — index

Retour : [README](../README.md) · Processus : [workflow](../gouvernance/workflow.md) · Rôle : [skills/auditeur](../skills/auditeur/SKILL.md)

Un audit **constate**, il ne corrige jamais. Chaque constat porte un ID `OBS-NN` global et unique, référencé partout ailleurs par cet ID.

## Rapports

| ID | Date | Périmètre | Statut | Fichier |
|---|---|---|---|---|
| AUDIT-001 | 2026-09-25 | Exploration initiale de tout le dépôt | `A_REVOIR` (Q-02 fond et Q-07 bis en suspens) | [AUDIT-001_exploration_initiale.md](AUDIT-001_exploration_initiale.md) |
| AUDIT-002 | 2026-09-25 | Map-matching des bus (GTFS → OSM), diagnostic chiffré | `A_REVOIR` | [AUDIT-002_map_matching_bus.md](AUDIT-002_map_matching_bus.md) |

## Registre des constats (vue rapide)

OBS-01 à OBS-20 : définis dans [AUDIT-001](AUDIT-001_exploration_initiale.md). OBS-21 à OBS-24 : définis dans [AUDIT-002](AUDIT-002_map_matching_bus.md).

| ID | Gravité | Sujet | Statut |
|---|---|---|---|
| OBS-01 | Haute | Vélo : SHP en Lambert-93 déclaré en 4326 (0 lien au lieu de 1 234) | RESOLU ([PLAN-001](../archive/plans/PLAN-001_sauvegarde_chargement_reseaux.md)) |
| OBS-02 | Haute | GTFSImporter : extraction SHP jamais exécutée (1er lancement cassé) | OUVERT |
| OBS-03 | Haute | Découpage TC sur le contour (`exterior`) du polygone | CONFIRME (23 arrêts dans la zone test, 0 retenu) |
| OBS-04 | Moyenne | `add_speed_when_missing` absent du pipeline actif | OUVERT |
| OBS-05 | Moyenne | `estimate_capacity` : KeyError si vitesse hors table | OUVERT |
| OBS-06 | Moyenne | CRS incohérents selon la méthode de sélection de zone | OUVERT |
| OBS-07 | Moyenne | Attente Streamlit infinie ; chemins relatifs au cwd | OUVERT |
| OBS-08 | Moyenne | Erreur OSM avalée ; double téléchargement OSM | OUVERT |
| OBS-09 | Basse | Héritage `AequilibraeBuilder(NetworkBuilder)` artificiel | OUVERT |
| OBS-10 | Moyenne | Tram/métro/funiculaire non construits (le map-matching réservé aux bus est voulu, A-04) | OUVERT · J3 (lignes propres) |
| OBS-11 | Basse | Agrégation IRIS : `assert` fragile, zones isolées | OUVERT |
| OBS-12 | Basse | `add_network_layer(draw_arrows=False)` → NameError | OUVERT |
| OBS-13 | Basse | Filtre « Walk Only » : priorité des opérateurs | OUVERT (intention à confirmer) |
| OBS-14 | Basse | Legacy `car.py` : anomalies toujours vides ; `load_zones` casse du nom | OUVERT |
| OBS-15 | Basse | Duplication map-matching (`load_network/pt.py`) + code mort | OUVERT |
| OBS-16 | Basse | Config : `argparse` inutilisable en CLI, `type=bool/list` (`save_path` ajouté par PLAN-001) | OUVERT |
| OBS-17 | Info | API dépréciée `unary_union` | OUVERT |
| OBS-18 | Moyenne | Hygiène du dépôt : pycache, notebooks lourds, artefacts suivis, pas d'env ni de tests | REPORTE (A-05) |
| OBS-19 | Info | `conversion_gtfs.py` non branché, dépendances non déclarées | OUVERT |
| OBS-20 | Haute (objectif) | Le réseau n'est pas encore « multimodal sur un même graphe » | OUVERT |
| OBS-21 | Haute | Map-matching par **fragment** de ligne (découpage avant projection) : 110 tronçons sur 127 sans tracé | CONFIRME (exécution) |
| OBS-22 | Haute | Tracés map-matchés éloignés du GTFS (Hausdorff médian 101 m, max 1,9 km) | CONFIRME (causes à vérifier) |
| OBS-23 | Moyenne | `pt_links_inside` dupliqué par trip (4 072 lignes pour 127 géométries) | OUVERT |
| OBS-24 | Basse | `final_matches` contient les liens de chemins écartés | OUVERT |
