---
role: plan
lecteurs: tous les agents ; l'utilisateur pour valider
maj: 2026-09-25
---

# Plans d'action — index

Retour : [README](../README.md) · Processus : [workflow](../gouvernance/workflow.md) · Modèle : [_modele_plan.md](_modele_plan.md)

## Deux niveaux de plans

| Niveau | Fichier | Contenu | Lecteurs |
|---|---|---|---|
| **Stratégique** (commun à tous) | [feuille_de_route.md](feuille_de_route.md) | objectifs du projet, jalons, ordre des chantiers | tous les agents |
| **Opérationnel** | `PLAN-NNN_<sujet>.md` | étapes précises, fichiers touchés, critères d'acceptation, rôle de chaque agent | l'agent exécutant + le relecteur |

Un plan opérationnel référence **toujours** les constats (`OBS-xx`) ou le jalon de la feuille de route qu'il traite.

## Cycle de vie

`BROUILLON` → `PROPOSE` (présenté à l'utilisateur) → `VALIDE` (accord explicite) → `EN_COURS` → `TERMINE` → résumé dans [archive/JOURNAL.md](../archive/JOURNAL.md) et fichier déplacé dans `archive/plans/`.

**Seul un plan `VALIDE` ou `EN_COURS` autorise un agent à modifier le code**, et seulement dans son périmètre.

## Plans

| ID | Sujet | Statut | Constats / jalon |
|---|---|---|---|
| PLAN-002 | [Affichage GTFS initial vs map-matché des bus (diagnostic)](PLAN-002_affichage_diagnostic_map_matching.md) | `EN_COURS` (revue OK, confirmation utilisateur attendue) | [AUDIT-002](../audit/AUDIT-002_map_matching_bus.md) · jalon J1 |

Plans terminés (archivés) : [PLAN-001 — Sauvegarde et chargement d'un réseau](../archive/plans/PLAN-001_sauvegarde_chargement_reseaux.md) (2026-09-25).

Feuille de route : [feuille_de_route.md](feuille_de_route.md) — statut `PROPOSE`.
