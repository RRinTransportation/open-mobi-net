---
role: skill (checklist)
lecteurs: agent dev (avant de rendre la main), auditeur (en revue)
maj: 2026-09-25
---

# Checklist de livraison (dev)

Retour : [dev/SKILL.md](SKILL.md)

## Périmètre
- [ ] `git diff --stat` ne touche **que** des fichiers listés dans le plan.
- [ ] Aucune modification de `data/`, pas de commit ni de push non demandés.
- [ ] Toute anomalie croisée est notée dans « Découvertes » du plan, pas corrigée.

## Justesse
- [ ] Chaque critère d'acceptation du plan est vérifié, avec la **manière** de le vérifier (commande, cellule, sortie observée).
- [ ] CRS explicites à chaque lecture/écriture géographique ([donnees_et_crs](../../architecture/donnees_et_crs.md)).
- [ ] Le notebook `build_networks.ipynb` s'exécute encore (au minimum sur une petite zone), ou l'impossibilité est signalée.
- [ ] Pas de nouveau chemin relatif fragile ni de valeur codée en dur qui aurait sa place dans la config.

## Base de connaissances
- [ ] Fiches `architecture/` impactées : lignes, signatures et flux mis à jour, `maj` modifié.
- [ ] Statut des `OBS-xx` traités passé à `RESOLU (PLAN-NNN)` dans [audit/README.md](../../audit/README.md), sous réserve de la revue.
- [ ] Plan coché ; [ETAT.md](../../ETAT.md) mis à jour.

## Compte rendu à l'utilisateur
- [ ] Fait / vérifié (avec preuves) / non fait et pourquoi / découvertes.
