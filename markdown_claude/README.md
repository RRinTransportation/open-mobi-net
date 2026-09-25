---
role: hub
lecteurs: tous les agents
maj: 2026-09-25
---

# markdown_claude — point d'entrée

Base de connaissances en **graphe de markdown** sur le dépôt MMNE (*Multi-Modal Network Extraction*).
Elle sert à coordonner les agents (auditeur, dev, …) tout en **limitant le contexte chargé** :
chaque agent lit ce fichier, puis [ETAT.md](ETAT.md), puis **uniquement** les nœuds utiles à sa tâche.

## 1. Règle d'or (s'applique à tous les agents)

> **Aucun agent ne modifie le code, les données ou la configuration sans une validation explicite préalable de l'utilisateur.**
> Le cycle est toujours : **Audit → Synthèse → Validation d'un plan → Production → Archivage.**
> Détail : [gouvernance/workflow.md](gouvernance/workflow.md).

## 2. Ordre de lecture recommandé

1. Ce fichier (≈ 2 min).
2. [ETAT.md](ETAT.md) : ce qui est en cours, les décisions en attente.
3. La fiche de ton rôle : [skills/README.md](skills/README.md) → `skills/<rôle>/SKILL.md`.
4. Les nœuds d'architecture utiles à ta tâche (table de routage ci-dessous).
5. **Ne pas lire** [archive/](archive/README.md) sauf demande explicite.

## 3. Table de routage — « je cherche… → je lis… »

| Je cherche… | Nœud |
|---|---|
| Vue globale du pipeline, carte des modules | [architecture/vue_ensemble.md](architecture/vue_ensemble.md) |
| Qui appelle quoi, dans quel ordre (notebook → sorties) | [architecture/pipeline_execution.md](architecture/pipeline_execution.md) |
| Graphe d'imports internes et dépendances externes | [architecture/graphe_dependances.md](architecture/graphe_dependances.md) |
| Fichiers d'entrée/sortie, arborescence `data/`, CRS | [architecture/donnees_et_crs.md](architecture/donnees_et_crs.md) |
| Paramètres (`config/`, `args`, `filter_args`) | [architecture/modules/config.md](architecture/modules/config.md) |
| Sélection de la zone d'étude, `MultiModalNetwork`, `NetworkBuilder`, Streamlit | [architecture/modules/orchestration.md](architecture/modules/orchestration.md) |
| Réseau routier OSM/AequilibraE, hypothèses voies/vitesses/capacités | [architecture/modules/reseau_routier.md](architecture/modules/reseau_routier.md) |
| Vélo et marche | [architecture/modules/velo_marche.md](architecture/modules/velo_marche.md) |
| GTFS, transport public, map-matching bus → OSM | [architecture/modules/transport_public.md](architecture/modules/transport_public.md) |
| Zones IRIS et agrégation | [architecture/modules/zones_iris.md](architecture/modules/zones_iris.md) |
| Carte Folium, couches, anomalies affichées | [architecture/modules/visualisation.md](architecture/modules/visualisation.md) |
| Code ancien / non branché (`load_network/*`, `Ignore/`, `conversion_gtfs.py`) | [architecture/modules/code_legacy.md](architecture/modules/code_legacy.md) |
| Vocabulaire (IRIS, ab/ba, modes `c/b/w/t`, GTFS…) | [architecture/glossaire.md](architecture/glossaire.md) |
| Constats d'audit (bugs, risques, dette) | [audit/README.md](audit/README.md) |
| Plans d'action (proposés / validés / en cours) | [plan/README.md](plan/README.md) |
| Conventions d'écriture de ces markdown | [gouvernance/conventions.md](gouvernance/conventions.md) |

## 4. Organisation du dossier

```text
markdown_claude/
├── README.md              ← hub (ce fichier)
├── ETAT.md                ← tableau de bord vivant : à lire à chaque session
├── gouvernance/           ← règles communes à TOUS les agents
│   ├── workflow.md        ← cycle Audit → Synthèse → Plan → Production → Archive
│   └── conventions.md     ← nommage, frontmatter, liens, identifiants
├── architecture/          ← connaissance stable du code (graphe de nœuds)
│   ├── vue_ensemble.md, pipeline_execution.md, graphe_dependances.md,
│   ├── donnees_et_crs.md, glossaire.md
│   └── modules/           ← une fiche par bloc fonctionnel
├── audit/                 ← rapports d'audit (constats, jamais de correctifs)
├── plan/                  ← plans d'action : proposés → validés → en cours
├── skills/                ← fiches de rôle par agent (auditeur, dev, …)
└── archive/               ← historique condensé, NE PAS LIRE sauf besoin explicite
```

## 5. Principes pour économiser le contexte

- **Un nœud = un sujet.** Les fiches module font < 150 lignes et renvoient vers les autres plutôt que de répéter.
- **Source unique de vérité** : un constat d'audit n'est décrit qu'une fois (dans `audit/`), les autres fiches y renvoient par son identifiant (`OBS-xx`).
- Les références au code utilisent `chemin/fichier.py:ligne` (état de l'arbre de travail à la date `maj` du fichier). Si le code a bougé, **vérifier avant de citer**.
- Ce qui est terminé part dans [archive/](archive/README.md) sous forme condensée ; `ETAT.md` et `plan/` ne gardent que le vivant.
