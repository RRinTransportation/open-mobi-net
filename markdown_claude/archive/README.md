---
role: archive
lecteurs: AUCUN agent par défaut — seulement sur demande explicite de l'utilisateur
maj: 2026-09-25
---

# Archive

> **Ne pas parcourir ce dossier** pour une tâche courante. Il sert uniquement à comprendre l'historique quand l'utilisateur le demande explicitement.

## Contenu
- [JOURNAL.md](JOURNAL.md) : une entrée condensée (≤ 10 lignes) par cycle terminé, de la plus récente à la plus ancienne.
- `plans/` : plans `TERMINE` ou `ABANDONNE`, déplacés tels quels depuis `plan/`.
- `audits/` : audits `REVU` dont tous les constats sont clos (`RESOLU` ou `REJETE`).

## Règle d'archivage
Quand un plan passe `TERMINE` : ajouter l'entrée au journal (quoi, pourquoi, constats résolus, fichiers principaux, décisions), déplacer le plan dans `plans/`, retirer la ligne de [ETAT.md](../ETAT.md) et mettre à jour [plan/README.md](../plan/README.md).
