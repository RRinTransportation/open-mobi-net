---
role: skill
lecteurs: tous les agents (pour trouver leur fiche de rôle)
maj: 2026-09-25
---

# Skills — fiches de rôle des agents

Retour : [README](../README.md) · Règles communes (priment sur les skills) : [workflow](../gouvernance/workflow.md), [conventions](../gouvernance/conventions.md)

| Rôle | Fiche | Intervient aux étapes | Peut modifier le code ? |
|---|---|---|---|
| **Auditeur** | [auditeur/SKILL.md](auditeur/SKILL.md) | 1. Audit · 2. Synthèse · 5. Revue | **Jamais** |
| **Dev** | [dev/SKILL.md](dev/SKILL.md) | 4. Production | Uniquement dans le périmètre d'un plan `VALIDE` |

Ressources par rôle :
- auditeur : [modele_rapport_audit.md](auditeur/modele_rapport_audit.md)
- dev : [checklist_livraison.md](dev/checklist_livraison.md)

## Ajouter un rôle

Créer `skills/<role>/SKILL.md` avec les mêmes sections (Mission · Autorisé · Interdit · Lectures minimales · Procédure · Livrable), puis l'ajouter à ce tableau. Rôles envisageables plus tard : *planificateur* (rédaction des `PLAN-NNN`), *data* (préparation de jeux de test).
