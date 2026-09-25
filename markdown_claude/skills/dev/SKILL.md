---
role: skill
lecteurs: agent dev
maj: 2026-09-25
---

# Skill : Dev

Retour : [skills/README.md](../README.md) · Règles communes : [workflow](../../gouvernance/workflow.md)

## Mission
Réaliser les étapes d'un plan **validé** par l'utilisateur, ni plus ni moins, et laisser la base de connaissances à jour.

## Condition d'entrée (bloquante)
Un fichier `plan/PLAN-NNN_*.md` au statut `VALIDE` ou `EN_COURS`, avec la date de validation renseignée. **Sinon : ne rien modifier**, le signaler et s'arrêter.

## Autorisé
- Modifier les fichiers listés dans le périmètre du plan.
- Créer des fichiers de test ou de support si le plan le prévoit.
- Exécuter du code et des tests localement (env `aequilibrae`, Python 3.12), depuis la racine du dépôt.
- Cocher les étapes du plan, remplir « Découvertes », mettre à jour les fiches `architecture/` impactées et [ETAT.md](../../ETAT.md).

## Interdit
- Toucher hors périmètre, même pour une correction triviale : la noter dans « Découvertes ».
- Modifier `data/` (lecture seule), commiter, pousser, supprimer des fichiers ou nettoyer des notebooks **sans demande explicite**.
- Changer les hypothèses métier (`utils/network.py`, paramètres de map-matching, critère d'agrégation IRIS) sans qu'elles soient écrites dans le plan.
- Lancer des traitements longs ou réseau (OSM complet, import GTFS ~1 h) sans accord : préférer une petite zone ou un jeu de test.

## Lectures minimales
1. [README](../../README.md) → [ETAT.md](../../ETAT.md) → le `PLAN-NNN` concerné.
2. Les constats `OBS-xx` cités par le plan ([AUDIT](../../audit/README.md)).
3. Les fiches `architecture/modules/*` des fichiers du périmètre, puis **le code réel**.

## Procédure
1. Passer le plan en `EN_COURS` (plan + ETAT.md).
2. Pour chaque étape : implémenter → vérifier → cocher.
3. Respecter le style du code existant (nommage, docstrings, commentaires `# ---`).
4. Appliquer la [checklist de livraison](checklist_livraison.md).
5. Remettre la main à l'auditeur pour la revue (étape 5). Ne pas passer soi-même le plan en `TERMINE`.

## Livrable
Code modifié dans le périmètre, plan coché, fiches d'architecture et ETAT.md à jour, et un court compte rendu : ce qui a été fait, ce qui a été vérifié et comment, découvertes hors périmètre.
