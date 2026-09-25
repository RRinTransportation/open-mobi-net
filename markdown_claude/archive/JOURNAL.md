---
role: archive
lecteurs: sur demande explicite uniquement
maj: 2026-09-25
---

# Journal condensé

## 2026-09-25 — PLAN-002 réalisé (confirmation attendue)
- Carte : couches « PT bus GTFS init - matched / not matched » (cause d'échec, Hausdorff), « PT bus map-matched » (ex « PT Lanes »), « PT bus OSM links used ».
- `MapMatchingPT2OSM.bus_routes_diagnostics` → `gtfs_network_builder.pt_bus_routes_init`, sauvegardé avec le réseau ; résultat du map-matching inchangé (non-régression vérifiée).
- `anomalies.ipynb` supprimé par l'utilisateur : contenu intégré à `build_networks.ipynb`.

## 2026-09-25 — AUDIT-002 (map-matching des bus) et PLAN-002 proposé
- Priorité donnée par l'utilisateur : reprendre le map-matching des bus et afficher le GTFS initial à côté du tracé map-matché.
- [AUDIT-002](../audit/AUDIT-002_map_matching_bus.md) : 17 tronçons sur 127 map-matchés, car les lignes sont découpées en fragments avant projection (OBS-21) ; tracés obtenus éloignés du GTFS (OBS-22).
- [PLAN-002](../plan/PLAN-002_affichage_diagnostic_map_matching.md) proposé (affichage de diagnostic, sans changer le résultat).
- Nouvelle convention : tout identifiant est cité avec son lien et un libellé.

## 2026-09-25 — PLAN-001 terminé ([plan archivé](plans/PLAN-001_sauvegarde_chargement_reseaux.md))
- `MultiModalNetwork.save()/load()` (GeoPackage + metadata.json, module `build_network/network_io.py`), `--save_path`, cellules du notebook.
- OBS-01 corrigé (vélo lu en 2154 : 1 234 liens au lieu de 0) ; couches `own_loaded_bikes` ajoutées à la demande de l'utilisateur.
- Vérifié : 3 tests hors ligne, aller-retour des 12 couches d'un réseau réel, même carte après `load` dans un processus neuf, sans réseau.
- Découverte : OBS-03 confirmé (0 arrêt retenu sur la zone test).
- Clôturé sur confirmation de l'utilisateur (critère QGIS sans objet : l'utilisateur travaille uniquement en Python / notebooks).

## 2026-09-25 — Réponses à l'AUDIT-001, PLAN-001 proposé
- Réponses utilisateur : priorité 1 = sauvegarde/chargement des réseaux ; tram/métro en lignes propres ; nettoyage reporté ; jeux de test = réseaux sauvegardés.
- OBS-01 confirmé par exécution (le pipeline actif passe par `add_bike_network`, pas par `load_network_from_preprocessed`).
- README racine : ajout de la phrase « zone d'étude = union des IRIS intersectés » (à la demande de l'utilisateur).
- PLAN-001 rédigé (`PROPOSE`), feuille de route mise à jour, Q-07 reformulée.

## 2026-09-25 — Création de la base `markdown_claude/` et AUDIT-001
- Cartographie complète du dépôt (architecture, flux, dépendances, données/CRS, glossaire).
- AUDIT-001 : 20 constats (OBS-01…20) et 7 questions (Q-01…07), statut `A_REVOIR`.
- Gouvernance posée : Audit → Synthèse → Validation → Production → Archive ; rôles auditeur et dev.
- Aucune modification de code.

## Antérieur à la base de connaissances (d'après `git log`, 8 commits)
- 2026-05-28 : premier commit ; pipeline `MultiModalNetwork` (zone Streamlit, OSM AequilibraE, vélo, GTFS + map-matching bus) ; ajout des zones IRIS et IRIS agrégées pour l'OD (`cec3cff`).
- 2026-06-05 : mises à jour du README.
- Non commité au 2026-09-25 : couche « Car anomalies », hypothèse (1,1) pour les voies NaN/NaN, clé de vitesse 10 km/h, `add_network_layer` paramétrable, section README sur les anomalies de voies.
