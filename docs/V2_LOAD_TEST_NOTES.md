# US-113 — Notes de test de charge (génération de miniatures)

**Story :** US-113 — Valider la robustesse sous charge
**Statut :** validé, aucun problème détecté
**Date :** 2026-07-10
**Environnement :** Windows 11, machine de dev locale, ffmpeg 8.1.2 (Gyan.FFmpeg, cf. US-110)

## Objectif

Vérifier que `core/thumbnail_generator.py::generate_thumbnail()` (US-111), qui repose sur un
sous-processus `ffmpeg` par fichier, tient la charge sur un nombre de fichiers représentatif
d'une playlist réaliste, avant de considérer F16 (miniatures) terminé.

## Méthodologie

- 20 fichiers vidéo synthétiques générés via `ffmpeg -f lavfi -i testsrc` (mire de test, pas de
  contenu réel nécessaire — seul le conteneur/codec et la présence d'un flux vidéo comptent pour
  `generate_thumbnail()`), répartis sur 3 formats :
  - 7 × `.mp4` (H.264)
  - 7 × `.mkv` (H.264)
  - 6 × `.webm` (VP9)
- Durées variées (2 à 4 secondes) et résolution 160×120 à 5 fps, pour rester rapide à générer
  sans influer sur la mesure (seule la génération de miniature via `generate_thumbnail()` est
  chronométrée, pas la génération des fixtures elles-mêmes).
- Script `generate_thumbnail()` appelé séquentiellement sur les 20 fichiers, avec un
  `cache_dir` dédié et vide au premier passage.
- Fichiers et cache générés dans un répertoire temporaire (hors dépôt), supprimés après le test.

## Résultats — premier passage (cache froid)

| Métrique | Valeur mesurée |
|---|---|
| Fichiers traités | 20 / 20 |
| Échecs | 0 |
| Temps cumulé | **4.924 s** |
| Temps moyen par fichier | **0.246 s** |
| Processus `ffmpeg` restants après exécution (`ps aux \| grep ffmpeg`) | **0** (aucun zombie) |

Détail par fichier (extrait représentatif — tous les fichiers ont un temps similaire, entre
0.221 s et 0.286 s, sans dérive notable ni ralentissement progressif sur la série) :

```
video_1_mp4.mp4:   0.229s -> OK
video_8_mkv.mkv:   0.252s -> OK
video_15_webm.webm: 0.254s -> OK
video_20_webm.webm: 0.221s -> OK
```

## Résultats — second passage (cache chaud)

Rejoué immédiatement après sur les mêmes 20 fichiers, cache déjà peuplé :

| Métrique | Valeur mesurée |
|---|---|
| Temps cumulé | **0.022 s** |
| Temps moyen par fichier | **0.001 s** |

Confirme que le cache disque (US-111, nommage par hash SHA-256 du chemin source) évite bien
toute réinvocation d'`ffmpeg` au second lancement — un facteur d'environ **220×** plus rapide.

## Vérification zombies

```bash
ps aux | grep -i ffmpeg | grep -v grep
```

Exécuté immédiatement après le premier passage (20 sous-processus `ffmpeg` lancés séquentiellement,
un par fichier, chacun attendu synchronement via `subprocess.run()` avant de passer au suivant) :
aucune ligne retournée. Chaque sous-processus se termine bien avant que
`generate_thumbnail()` ne retourne — cohérent avec l'implémentation (`subprocess.run()` est
bloquant côté appelant, pas de `Popen` détaché).

## Conclusion

Le choix architectural F16 (sous-processus `ffmpeg`, un par fichier, invocation synchrone dans
`generate_thumbnail()`, parallélisée côté UI via `QThreadPool` en US-112) tient la charge sur 20
fichiers de formats variés (MP4/MKV/WebM) : temps cumulé de l'ordre de 5 secondes à froid,
quasi instantané à chaud, aucun processus zombie. Aucun problème de fuite de processus ou de
lenteur excessive détecté — **aucune story de correction n'est nécessaire**.

## Limites de ce test

- Fichiers synthétiques de très courte durée (2-4 s) et faible résolution (160×120) : ne
  reproduit pas le coût d'un `ffmpeg -i` sur un fichier volumineux réel (métadonnées plus
  riches, décodage initial plus long sur un flux 1080p/4K). À revalider avec des fichiers réels
  si des retours utilisateur signalent une lenteur en usage réel.
- Exécution séquentielle (pas de parallélisme) dans ce script de validation, alors que
  l'UI réelle (US-112) parallélise via `QThreadPool` — un test avec plusieurs sous-processus
  `ffmpeg` concurrents pourrait révéler une contention CPU/E-S différente ; non mesuré ici.
- Une seule exécution machine (Windows, cette machine de dev) : pas de comparaison macOS/Linux.
