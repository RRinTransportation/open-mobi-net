---
role: skill (modèle)
lecteurs: agent auditeur
maj: 2026-09-25
---

# Modèle de rapport d'audit

Copier le bloc ci-dessous dans `audit/AUDIT-NNN_<sujet>.md`. Exemple complet : [AUDIT-001](../../audit/AUDIT-001_exploration_initiale.md).

```markdown
---
role: audit
lecteurs: utilisateur (synthèse), auditeur, dev
maj: AAAA-MM-JJ
statut: EN_COURS
---

# AUDIT-NNN — <Périmètre>

Index : [audit/README.md](README.md)

**Méthode** : <ce qui a été lu, exécuté ou non exécuté>. **Aucune modification n'a été faite.**
Confiance : C = constaté · P = probable · V = à vérifier par exécution.

## Synthèse
1. …
Priorités suggérées : …

## Constats détaillés
### OBS-NN — <titre> · <Gravité> · <C|P|V>
- **Où** : [fichier.py:ligne](../../chemin/fichier.py#Lligne)
- **Constat** : …
- **Effet** : …
- **Piste** (facultatif, sans code) : …

## Questions ouvertes pour l'utilisateur
- **Q-NN** — …
```
