---
role: règles communes
lecteurs: tous les agents qui écrivent dans markdown_claude/
maj: 2026-09-25
---

# Conventions d'écriture

Retour : [README.md](../README.md) · [workflow.md](workflow.md)

## Frontmatter obligatoire

Chaque fichier commence par :

```yaml
---
role: <hub | tableau de bord | règles communes | architecture | audit | plan | skill | archive>
lecteurs: <qui doit lire ce fichier>
maj: AAAA-MM-JJ
statut: <optionnel, pour audits et plans>
---
```

## Identifiants

| Préfixe | Objet | Exemple | Unicité |
|---|---|---|---|
| `AUDIT-NNN` | rapport d'audit | `AUDIT-001` | global |
| `OBS-NN` | constat d'audit | `OBS-07` | global (on ne réutilise jamais un numéro) |
| `PLAN-NNN` | plan d'action | `PLAN-001` | global |
| `Q-NN` | question ouverte à l'utilisateur | `Q-03` | global |

Nom de fichier : `<ID>_<sujet_court_snake_case>.md` (ex. `PLAN-001_corrections_crs.md`).

## Liens

- Toujours en **chemin relatif** : `[texte](../architecture/modules/zones_iris.md)`.
- Code : `` `load_network/iris.py:181` `` (chemin depuis la racine du dépôt + ligne). Pour un lien cliquable depuis `markdown_claude/`, préfixer par `../../` selon la profondeur.
- Référencer un constat par son ID plutôt que de le redécrire, **mais jamais un ID seul** : toujours le lien vers le markdown où il est défini **et** un libellé court.
  - Exemple : « [OBS-03](../audit/AUDIT-001_exploration_initiale.md) — découpage TC sur le contour du polygone ».
  - Une section qui cite plusieurs IDs d'un même document commence par le lien vers ce document.
  - Vaut pour `OBS-xx`, `Q-xx`, `PLAN-NNN`, `AUDIT-NNN` et les jalons `Jx` de la [feuille de route](../plan/feuille_de_route.md), dans les markdown **et** dans les réponses à l'utilisateur.

## Taille et style

- Fiche module ≤ 150 lignes ; fichier de plan ≤ 200 lignes. Au-delà, découper en nœuds reliés.
- Rédaction en français ; noms de code, colonnes, fonctions en anglais tels quels.
- Des tableaux et des listes plutôt que de la prose ; un diagramme mermaid quand un flux doit être visualisé.
- Distinguer ce qui est **constaté** (lu dans le code), **probable** (déduit) et **à vérifier** (demande une exécution).

## Mise à jour des fiches `architecture/`

Une fiche d'architecture décrit **l'état actuel** du code. Après une production validée, le dev met à jour les fiches impactées (lignes, signatures, flux) dans la même livraison.
