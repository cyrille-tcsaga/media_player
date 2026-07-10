# PRD V2 — Lecteur Audio/Vidéo PyQt6 + QtMultimedia

**Document compagnon de** `PRD_Lecteur_Media_PyQt6.md` (V1/MVP, statut : terminé) **et** `USER_STORIES_Lecteur_Media_PyQt6.md`
**Statut :** Draft V1
**Date :** Juillet 2026
**Prérequis :** MVP V1 complet et validé (packaging PyInstaller fonctionnel confirmé)

---

## 1. Contexte et objectif

Le MVP (V1) est fonctionnel : lecture audio/vidéo basique, playlist simple, gestion d'erreurs, packaging macOS. Cette V2 formalise les fonctionnalités identifiées comme V2/nice-to-have dans le PRD V1 (section 3.2, F12 à F19), en un plan de développement structuré et actionnable.

**Principe directeur de la V2 :** contrairement au MVP qui partait d'une base vierge, la V2 modifie et étend une base de code existante, déjà testée et packagée. Chaque story V2 doit donc explicitement traiter deux aspects que le MVP n'avait pas à gérer :
1. **Impact sur le code existant** : quelles classes/fichiers du MVP sont modifiés, quels tests existants risquent de casser
2. **Migration des données/comportements** : si un comportement V1 documenté (ex. `PlaylistManager` qui bloque en fin de liste) change de sens en V2, cela doit être tranché explicitement, pas halluciné en cours de route

**Non-objectifs (toujours hors scope, hérités du PRD V1) :**
- Streaming réseau (HTTP/RTSP)
- Conversion/transcodage de fichiers
- Édition vidéo
- Support plugin/extension tiers
- Synchronisation cloud ou bibliothèque multi-appareils
- Support DRM, égaliseur audio avancé, enregistrement/capture

---

## 2. Récapitulatif des fonctionnalités V2

| # | Fonctionnalité | Complexité estimée | Modifie du code V1 existant ? |
|---|---|---|---|
| F12 | Persistance de la playlist (JSON) | Faible | Non (nouveau composant) |
| F13 | Mode répétition (aucune/piste/playlist) | Moyenne | **Oui** — `PlaylistManager.next()/previous()` |
| F14 | Mode aléatoire (shuffle) | Moyenne | **Oui** — `PlaylistManager.next()/previous()` |
| F15 | Thème sombre/clair | Faible | Non (couche de présentation additive) |
| F16 | Miniatures vidéo dans la playlist | Élevée | Non (nouveau composant), mais risque technique hérité du spike |
| F17 | Sous-titres externes (.srt) | Élevée | Oui — `ui/video_widget.py` (overlay) |
| F18 | Vitesse de lecture (0.5x-2x) | Faible | Oui — `core/player_engine.py` (une méthode) |
| F19 | Mini-mode (fenêtre compacte, always-on-top) | Moyenne | Non (nouvelle fenêtre), mais partage l'état avec `MainWindow` |
| F20 | Plein écran pour la vidéo | Faible | Non (extension de `MainWindow`/`video_widget.py`) |

**Ordre de développement recommandé :** F12 → F18 → F20 → F13/F14 → F15 → F19 → F16 → F17, du plus simple/isolé au plus complexe/risqué. F16 et F17 sont volontairement traités en dernier : ce sont les deux fonctionnalités à plus fort risque technique (voir section 5).

---

## 3. Détail par fonctionnalité

### 3.1 F12 — Persistance de la playlist

**Description :** sauvegarder automatiquement la playlist courante dans un fichier JSON local, et la recharger au démarrage de l'application.

**Composants concernés :**
- Nouveau : `core/playlist_persistence.py` — sérialisation/désérialisation de `list[MediaItem]` vers/depuis un fichier JSON dédié (ex. `~/Library/Application Support/MediaPlayer/playlist.json` sur macOS)
- `core/playlist_manager.py` : ajout d'une méthode `save_to(path)` / `load_from(path)` ou délégation complète à `playlist_persistence.py` (préférer la délégation pour ne pas alourdir `PlaylistManager`)

**Décision actée (cf. section 9) :** playlist et préférences sont stockées dans deux fichiers JSON distincts (`playlist.json` et `settings.json`), et non fusionnées dans un fichier unique. Ce choix isole les deux responsabilités : une corruption ou un format invalide sur l'un n'affecte pas l'autre, et chaque fichier peut évoluer indépendamment sans risquer de migration de schéma croisée.

**Points d'attention :**
- Un `MediaItem` référence un `file_path` — au rechargement, vérifier que le fichier existe toujours (`Path.exists()`) avant de l'ajouter à la playlist reconstituée ; sinon, comportement cohérent avec F10 (gestion d'erreurs V1) : signaler les fichiers manquants sans planter
- Sauvegarde déclenchée à chaque modification de la playlist (ajout/suppression) plutôt qu'uniquement à la fermeture de l'application, pour survivre à un crash

### 3.2 F13 — Mode répétition

**Description :** trois modes — aucune répétition (comportement V1 actuel), répétition d'une seule piste, répétition de toute la playlist.

**Impact sur le code existant (à traiter explicitement) :**
Le PRD V1 (US-040) a figé un comportement précis pour `PlaylistManager.next()` : blocage au dernier élément, pas de bouclage. La V2 doit changer cette méthode sans casser le test existant `tests/test_playlist_manager.py` qui valide ce comportement V1.

**Approche recommandée :** ajouter un paramètre `repeat_mode: RepeatMode` (nouvelle enum dans `core/models.py` : `NONE`, `TRACK`, `PLAYLIST`) à `PlaylistManager`, avec `NONE` comme valeur par défaut. Le test V1 existant reste valide tel quel (comportement par défaut inchangé) ; de nouveaux tests couvrent `TRACK` et `PLAYLIST`.

### 3.3 F14 — Mode aléatoire

**Description :** lecture des pistes de la playlist dans un ordre aléatoire, sans répétition avant d'avoir parcouru toute la liste une fois.

**Composants concernés :** `core/playlist_manager.py` (même remarque que F13 sur la non-régression), potentiellement un nouveau composant `core/shuffle_strategy.py` si la logique devient trop complexe pour rester dans `PlaylistManager`.

**Point d'attention :** définir précisément l'algorithme (ex. Fisher-Yates sur une copie de la liste, recalculé à chaque activation du mode shuffle plutôt qu'à chaque appel de `next()`) pour éviter les répétitions rapprochées perçues comme "pas vraiment aléatoire" par l'utilisateur — un piège UX classique du shuffle naïf.

### 3.4 F15 — Thème sombre/clair

**Description :** bascule entre un thème sombre et un thème clair, avec persistance du choix (réutilise F12/le même mécanisme de settings).

**Composants concernés :**
- Nouveau : `ui/theme_manager.py` — applique une feuille de style Qt (QSS) selon le thème sélectionné
- Nouveau : `core/settings_manager.py` — sérialisation/désérialisation des préférences (thème, dernier volume, etc.) vers/depuis `settings.json`, fichier distinct de `playlist.json` (cf. décision F12)

**Point d'attention :** détecter le thème système macOS au premier lancement (`QApplication` expose des informations de palette système) comme valeur par défaut, plutôt que de forcer un thème arbitraire.

### 3.5 F16 — Miniatures vidéo dans la playlist

**Description :** afficher une vignette représentative pour chaque fichier vidéo dans `PlaylistWidget`.

**Risque technique hérité du spike (US-002) :** deux approches étaient envisageables, avec des compromis différents :

1. **Via `QMediaPlayer` + `QVideoSink`** : charger chaque fichier, seek à une position, capturer une frame, puis arrêter/détruire le lecteur. Risque direct : c'est exactement le pattern qui a causé le hang sur `stop()` documenté dans `BACKEND_NOTES.md` pendant la Phase 0. Le correctif appliqué en V1 (attacher un `QVideoSink`) résout le cas isolé du spike, mais rien ne garantit sa stabilité sur un usage répété et en boucle (génération de dizaines de miniatures d'affilée) — c'est précisément le genre de scénario cumulatif qui n'a pas été testé.
2. **Via un appel `ffmpeg` en sous-processus** (extraction d'une frame en une commande, ex. `ffmpeg -ss 00:00:05 -i input.mkv -frames:v 1 output.jpg`) : robuste, découplé de `QMediaPlayer` et de tout risque de hang du backend Qt Multimedia, mais introduit une dépendance externe explicite à un binaire `ffmpeg` (distinct des bibliothèques FFmpeg déjà utilisées en interne par Qt) à bundler dans le packaging PyInstaller.

**Décision actée :** option 2 retenue comme approche principale, pas comme repli. Raisonnement : le hang documenté en Phase 0 est un comportement du backend Qt Multimedia sur lequel on n'a aucune garantie de stabilité à long terme (versions futures de Qt, usage répété non testé) — c'est un risque qu'on ne contrôle pas. À l'inverse, la dépendance à un binaire `ffmpeg` externe est un risque connu, borné, et entièrement sous contrôle (bundling explicite, testable une fois pour toutes). Entre un risque incertain et récurrent et un risque certain mais maîtrisable, la seconde option est la plus sûre pour une fonctionnalité qui tourne en boucle sur potentiellement des dizaines de fichiers.

**Conséquence pratique :**
- Le binaire `ffmpeg` doit être bundlé explicitement dans l'exécutable PyInstaller (et non simplement supposé présent sur la machine de l'utilisateur), pour ne pas casser la promesse d'exécutable autonome actée en V1 (US-060)
- `core/thumbnail_generator.py` invoque `ffmpeg` via `subprocess.run()`, avec gestion explicite du cas où l'extraction échoue (fichier corrompu, timeout) — dégradation gracieuse vers une icône générique plutôt qu'un crash
- Le test de charge (20+ fichiers) reste pertinent mais change de nature : il ne s'agit plus de vérifier l'absence de hang côté Qt, mais la robustesse et la performance de l'invocation répétée du sous-processus (temps d'exécution cumulé, gestion de processus zombies en cas d'échec)

**Composants concernés :** nouveau `core/thumbnail_generator.py`, cache disque des miniatures (`~/Library/Caches/MediaPlayer/thumbnails/`) pour éviter de régénérer à chaque lancement.

### 3.6 F17 — Sous-titres externes

**Description :** charger un fichier `.srt` associé à une vidéo et afficher les sous-titres en overlay.

**Point de vigilance majeur :** QtMultimedia (`QMediaPlayer`) n'a pas de rendu de sous-titres intégré pour des fichiers `.srt` externes chargés manuellement (contrairement aux pistes de sous-titres embarquées dans certains conteneurs, gérées différemment). Il faut :
1. Parser le fichier `.srt` soi-même (format simple, mais attention à l'encodage — UTF-8 vs Latin-1 selon la provenance du fichier)
2. Afficher le texte correspondant à la position de lecture courante dans un `QLabel` superposé au `QVideoWidget` (positionnement absolu ou layout dédié)
3. Synchroniser l'affichage avec `positionChanged` du lecteur, avec une tolérance de quelques centaines de ms

**Composants concernés :** nouveau `core/subtitle_parser.py` (parsing .srt), nouveau `ui/subtitle_overlay.py` (widget de superposition)

### 3.7 F18 — Vitesse de lecture

**Description :** ajuster la vitesse de lecture de 0.5x à 2x.

**Composants concernés :** `core/player_engine.py` — ajout d'une méthode `set_playback_rate(rate: float)` déléguant directement à `QMediaPlayer.setPlaybackRate()`. C'est la fonctionnalité V2 la plus simple, purement additive, aucun risque de régression identifié.

### 3.8 F19 — Mini-mode

**Description :** basculer vers une fenêtre compacte, toujours au premier plan, affichant uniquement la vidéo et des contrôles minimalistes.

**Composants concernés :** nouveau `ui/mini_mode_window.py`, partageant le même `PlayerViewModel` que `MainWindow` (pas de nouvelle instance de `PlayerEngine` — un seul lecteur actif, juste une vue différente dessus).

**Point d'attention architecture :** c'est le test le plus direct de la solidité du pattern MVVM du PRD V1 — si `MainWindow` et `MiniModeWindow` peuvent toutes deux s'abonner au même `PlayerViewModel` sans dupliquer d'état ni se désynchroniser, l'architecture V1 est validée a posteriori. Si ce n'est pas le cas facilement, c'est un signal que le ViewModel V1 a accumulé de la logique qui aurait dû rester dans `core/`.

### 3.9 F20 — Plein écran pour la vidéo

**Description :** basculer la zone vidéo (ou toute la fenêtre) en plein écran, via double-clic sur la vidéo ou raccourci clavier, avec sortie via Échap ou re-double-clic.

**Composants concernés :** `ui/main_window.py` (ou `ui/video_widget.py` selon que le plein écran couvre toute la fenêtre ou seulement la zone vidéo — recommandation : toute la fenêtre via `MainWindow.showFullScreen()`/`showNormal()`, plus simple à maintenir cohérent avec les contrôles existants que de sortir la zone vidéo dans une fenêtre séparée).

**Points d'attention :**
- Raccourci recommandé : double-clic sur `QVideoWidget` pour entrer, `Échap` pour sortir — cohérent avec les conventions établies par la plupart des lecteurs vidéo
- **Scope volontairement minimal pour la V2** : le plein écran de base n'implique pas de masquage automatique des contrôles après inactivité de la souris. Cette dernière partie (timer + `mouseMoveEvent` pour réafficher les contrôles au mouvement de la souris, puis les masquer après quelques secondes d'inactivité) est reportée en V3 si elle n'est pas jugée prioritaire — elle ajoute de la complexité UX sans changer la fonctionnalité de base
- Vérifier le comportement avec le mini-mode (F19) : le plein écran doit être désactivé ou clairement redéfini quand le mini-mode est actif, pour éviter un état ambigu entre les deux fenêtres

**Aucun impact sur `core/`** — cette fonctionnalité est purement une question de présentation, sans risque de régression sur la logique métier testée en V1.

---

## 4. Nouveaux composants d'architecture (vue d'ensemble)

```
media_player/
├── core/
│   ├── playlist_persistence.py   # NOUVEAU (F12) — playlist.json
│   ├── settings_manager.py       # NOUVEAU (F15) — settings.json, fichier distinct de playlist.json
│   ├── shuffle_strategy.py       # NOUVEAU si nécessaire (F14)
│   ├── thumbnail_generator.py    # NOUVEAU (F16) — invoque ffmpeg en sous-processus
│   ├── subtitle_parser.py        # NOUVEAU (F17)
│   ├── models.py                 # MODIFIÉ — ajout enum RepeatMode (F13)
│   ├── playlist_manager.py       # MODIFIÉ — repeat_mode, shuffle (F13, F14)
│   └── player_engine.py          # MODIFIÉ — set_playback_rate (F18)
├── ui/
│   ├── theme_manager.py          # NOUVEAU (F15)
│   ├── mini_mode_window.py       # NOUVEAU (F19)
│   ├── subtitle_overlay.py       # NOUVEAU (F17)
│   ├── playlist_widget.py        # MODIFIÉ — affichage miniatures (F16)
│   └── video_widget.py           # MODIFIÉ — intégration overlay (F17)
└── tests/
    ├── test_playlist_persistence.py   # NOUVEAU
    ├── test_thumbnail_generator.py    # NOUVEAU
    ├── test_subtitle_parser.py        # NOUVEAU
    └── test_playlist_manager.py       # ENRICHI (F13, F14) sans régression sur les tests V1 existants
```

---

## 5. Exigences non fonctionnelles (V2)

| Catégorie | Exigence |
|---|---|
| Non-régression | 100% des tests V1 existants continuent de passer sans modification de leurs assertions (seuls de nouveaux tests s'ajoutent) |
| Performance | Génération de miniatures : ne doit pas bloquer l'UI (traitement asynchrone ou en arrière-plan, ex. `QThread` ou `QThreadPool`) |
| Robustesse | Un fichier `.srt` mal formé ne doit pas empêcher la lecture vidéo (dégradation gracieuse : vidéo sans sous-titres + message discret) |
| Maintenabilité | Couverture de tests >= 70% maintenue sur l'ensemble de `core/`, nouveaux fichiers inclus |
| Compatibilité | Toutes les fonctionnalités V2 doivent fonctionner sur macOS (plateforme validée en V1) ; pas d'extension du périmètre plateforme dans cette V2 |

---

## 6. Plan de développement

| Phase | Contenu | Sortie attendue |
|---|---|---|
| Phase 7 — Persistance & réglages | F12, socle `app_settings.py` | Playlist et préférences survivent à un redémarrage |
| Phase 8 — Vitesse, plein écran & thème | F18, F20, F15 | Fonctionnalités additives à faible risque, livrées rapidement |
| Phase 9 — Répétition & aléatoire | F13, F14 | `PlaylistManager` étendu, non-régression validée par les tests V1 existants |
| Phase 10 — Mini-mode | F19 | Validation croisée de l'architecture MVVM V1 |
| Phase 11 — Miniatures | F16 (extraction `ffmpeg` en sous-processus) | Test de charge sur la robustesse/performance de l'invocation répétée du sous-processus, packaging du binaire `ffmpeg` validé |
| Phase 12 — Sous-titres | F17 | Dernière phase, la plus complexe ; peut être reportée à une V3 si le budget temps V2 est dépassé |

**Remarque :** contrairement au découpage V1 où chaque phase était strictement séquentielle, les phases 7 à 10 de la V2 sont largement indépendantes entre elles et peuvent être réordonnées selon ta disponibilité (samedis) sans risque d'interblocage. Seules les phases 11 et 12 doivent rester en fin de parcours, pour les raisons de risque technique détaillées en section 3.5 et 3.6.

---

## 7. Critères d'acceptation (Definition of Done de la V2)

La V2 est considérée complète quand :

1. La playlist et les préférences (thème, dernier volume) sont restaurées après redémarrage de l'application
2. Les trois modes de répétition fonctionnent, ainsi que le mode aléatoire, sans régression sur le comportement V1 par défaut
3. Le thème sombre/clair peut être basculé et persiste entre les sessions
4. La vitesse de lecture est ajustable de 0.5x à 2x sans artefact audio/vidéo majeur
5. Le plein écran peut être activé/désactivé via double-clic et raccourci clavier, sans conflit d'état avec le mini-mode
6. Le mini-mode reflète en temps réel l'état de lecture du lecteur principal, dans les deux sens (contrôler depuis le mini-mode affecte la fenêtre principale et vice-versa)
7. Les miniatures s'affichent dans la playlist pour au moins 95% des formats vidéo supportés en V1, sans hang reproductible sur un test de charge de 20+ fichiers
8. Les sous-titres `.srt` s'affichent synchronisés à la lecture, avec dégradation gracieuse sur fichier malformé
9. 100% des tests V1 existants passent toujours, en plus des nouveaux tests V2
10. Couverture de tests globale sur `core/` >= 70% maintenue

---

## 8. Risques identifiés

| Risque | Impact | Mitigation |
|---|---|---|
| Récurrence du hang `QVideoSink`/`stop()` en génération de miniatures répétée | Éliminé | Option écartée (cf. section 3.5) — extraction via `ffmpeg` en sous-processus retenue dès le départ, sans dépendre du pipeline `QMediaPlayer` |
| Régression silencieuse sur `PlaylistManager.next()/previous()` (F13/F14) | Élevé | Les tests V1 existants ne doivent jamais être modifiés dans leurs assertions ; toute évolution de comportement passe par un nouveau paramètre à valeur par défaut rétrocompatible |
| Alourdissement de l'exécutable packagé (miniatures, sous-titres, thèmes) | Moyen | Mesurer la taille de l'exécutable avant/après chaque fonctionnalité, documenter dans le README si elle dépasse un seuil raisonnable |
| Dépendance à un binaire `ffmpeg` externe pour F16 | Moyen | Bundler explicitement le binaire dans le packaging PyInstaller (US-060 étendu) plutôt que de supposer sa présence système ; documenter cette dépendance comme distincte des bibliothèques FFmpeg internes à Qt |
| Dérive de scope vers une V3 non planifiée | Faible | Les phases 11/12 sont explicitement identifiées comme reportables ; ne pas ajouter de nouvelle fonctionnalité non listée en section 2 sans révision formelle de ce PRD |

---

## 9. Décisions actées

1. **Mécanisme de settings :** deux fichiers JSON séparés — `playlist.json` (F12) et `settings.json` (F15) — plutôt qu'un fichier unique. Isole les deux responsabilités et évite qu'une corruption ou une évolution de schéma sur l'un affecte l'autre.
2. **F16 (miniatures) :** extraction via `ffmpeg` en sous-processus retenue comme approche principale (et non comme repli). Le risque de hang côté `QVideoSink`/backend Qt Multimedia, documenté en Phase 0, est un risque non maîtrisé qu'on préfère éviter entièrement plutôt que de le tester en espérant qu'il ne se reproduise pas à l'échelle. La dépendance à un binaire `ffmpeg` bundlé est un risque connu et borné, jugé plus sûr.
3. **F17 (sous-titres) :** reste dans le périmètre V2 (Phase 12), pas d'isolement en V3 pour le moment. Cette décision n'est pas gravée dans le marbre — si le temps manque en fin de V2, la section 8 (risques) prévoit déjà cette possibilité de report.

---
---

# PRD V2 (English) — Audio/Video Player, PyQt6 + QtMultimedia

**Companion document to** `PRD_Lecteur_Media_PyQt6.md` (V1/MVP, status: complete) **and** `USER_STORIES_Lecteur_Media_PyQt6.md`
**Status:** Draft V1
**Date:** July 2026
**Prerequisite:** V1 MVP complete and validated (working PyInstaller packaging confirmed)

---

## 1. Background and objective

The MVP (V1) is functional: basic audio/video playback, a simple playlist, error handling, and macOS packaging. This V2 formalises the features identified as V2/nice-to-have in the V1 PRD (section 3.2, F12 through F19) into a structured, actionable development plan.

**Guiding principle for V2:** unlike the MVP, which started from a blank slate, V2 modifies and extends an existing codebase that is already tested and packaged. Every V2 story must therefore explicitly address two aspects the MVP did not need to worry about:
1. **Impact on existing code** — which V1 classes/files are modified, and which existing tests are at risk of breaking
2. **Migration of data/behaviour** — if a documented V1 behaviour (e.g. `PlaylistManager` stopping at the end of the list) changes meaning in V2, that must be explicitly decided, not silently reinterpreted mid-implementation

**Non-goals (still out of scope, inherited from the V1 PRD):**
- Network streaming (HTTP/RTSP)
- File conversion/transcoding
- Video editing
- Third-party plugin/extension support
- Cloud synchronisation or multi-device library
- DRM support, an advanced audio equaliser, or recording/capture

---

## 2. Feature overview for V2

| # | Feature | Estimated complexity | Modifies existing V1 code? |
|---|---|---|---|
| F12 | Playlist persistence (JSON) | Low | No (new component) |
| F13 | Repeat mode (none/track/playlist) | Medium | **Yes** — `PlaylistManager.next()/previous()` |
| F14 | Shuffle mode | Medium | **Yes** — `PlaylistManager.next()/previous()` |
| F15 | Dark/light theme | Low | No (additive presentation layer) |
| F16 | Video thumbnails in the playlist | High | No (new component), but inherits a technical risk from the spike |
| F17 | External subtitles (.srt) | High | Yes — `ui/video_widget.py` (overlay) |
| F18 | Playback speed (0.5x–2x) | Low | Yes — `core/player_engine.py` (a single method) |
| F19 | Mini-mode (compact, always-on-top window) | Medium | No (new window), but shares state with `MainWindow` |
| F20 | Fullscreen video | Low | No (extension of `MainWindow`/`video_widget.py`) |

**Recommended development order:** F12 → F18 → F20 → F13/F14 → F15 → F19 → F16 → F17, from simplest/most isolated to most complex/riskiest. F16 and F17 are deliberately handled last: they are the two highest-technical-risk features (see section 5).

Compared with the French version's ordering rationale, it is worth being explicit about *why* this particular order rather than, say, tackling F13/F14 first simply because they were listed earlier in the V1 PRD: sequencing by risk rather than by feature-list order means that if time runs out partway through V2, what gets dropped is the riskiest, most schedulable-into-a-later-release work (thumbnails, subtitles) rather than the low-risk quality-of-life features users are most likely to notice missing day to day (persistence, playback speed).

---

## 3. Feature detail

### 3.1 F12 — Playlist persistence

**Description:** automatically save the current playlist to a local JSON file, and reload it when the application starts.

**Components involved:**
- New: `core/playlist_persistence.py` — serialisation/deserialisation of `list[MediaItem]` to/from a dedicated JSON file (e.g. `~/Library/Application Support/MediaPlayer/playlist.json` on macOS)
- `core/playlist_manager.py`: add `save_to(path)` / `load_from(path)` methods, or delegate entirely to `playlist_persistence.py` (delegation is preferred, to avoid bloating `PlaylistManager`)

**Decision made (see section 9):** the playlist and preferences are stored in two separate JSON files (`playlist.json` and `settings.json`), rather than merged into a single file. This isolates the two responsibilities: corruption or an invalid format in one does not affect the other, and each file can evolve independently without risking a cross-cutting schema migration.

**Points of attention:**
- A `MediaItem` references a `file_path` — on reload, check that the file still exists (`Path.exists()`) before adding it back to the reconstructed playlist; otherwise, behave consistently with F10 (V1 error handling): flag missing files without crashing
- Save on every playlist modification (add/remove) rather than only on application exit, so state survives a crash

### 3.2 F13 — Repeat mode

**Description:** three modes — no repeat (current V1 behaviour), repeat a single track, repeat the whole playlist.

**Impact on existing code (must be explicitly addressed):**
The V1 PRD (US-040) locked down a specific behaviour for `PlaylistManager.next()`: stopping at the last item, with no wraparound. V2 must change this method without breaking the existing `tests/test_playlist_manager.py` test that validates this V1 behaviour.

**Recommended approach:** add a `repeat_mode: RepeatMode` parameter (a new enum in `core/models.py`: `NONE`, `TRACK`, `PLAYLIST`) to `PlaylistManager`, with `NONE` as the default value. The existing V1 test remains valid as-is (default behaviour unchanged); new tests cover `TRACK` and `PLAYLIST`.

### 3.3 F14 — Shuffle mode

**Description:** play the playlist's tracks in random order, without repeating any track before the whole list has been played through once.

**Components involved:** `core/playlist_manager.py` (same non-regression note as F13), potentially a new `core/shuffle_strategy.py` component if the logic becomes too complex to remain inside `PlaylistManager`.

**Point of attention:** define the algorithm precisely (e.g. a Fisher–Yates shuffle over a copy of the list, recomputed each time shuffle mode is enabled rather than on every `next()` call) to avoid closely-spaced repeats that users perceive as "not really random" — a classic UX pitfall of naive shuffling.

### 3.4 F15 — Dark/light theme

**Description:** toggle between a dark and a light theme, with the choice persisted (reusing F12's settings mechanism).

**Components involved:**
- New: `ui/theme_manager.py` — applies a Qt stylesheet (QSS) according to the selected theme
- New: `core/settings_manager.py` — serialisation/deserialisation of preferences (theme, last volume, etc.) to/from `settings.json`, a file separate from `playlist.json` (see the F12 decision)

**Point of attention:** detect the macOS system theme on first launch (`QApplication` exposes system palette information) as the default value, rather than forcing an arbitrary theme.

### 3.5 F16 — Video thumbnails in the playlist

**Description:** display a representative thumbnail for each video file in `PlaylistWidget`.

**Technical risk inherited from the spike (US-002):** two approaches were on the table, with different trade-offs:

1. **Via `QMediaPlayer` + `QVideoSink`**: load each file, seek to a position, capture a frame, then stop/destroy the player. Direct risk: this is exactly the pattern that caused the `stop()` hang documented in `BACKEND_NOTES.md` during Phase 0. The fix applied in V1 (attaching a `QVideoSink`) resolves the spike's isolated case, but there is no guarantee of stability under repeated, looped use (generating dozens of thumbnails in a row) — precisely the kind of cumulative scenario that was never tested.
2. **Via a subprocess call to `ffmpeg`** (extracting one frame in a single command, e.g. `ffmpeg -ss 00:00:05 -i input.mkv -frames:v 1 output.jpg`): robust, decoupled from `QMediaPlayer` and from any Qt Multimedia backend hang risk, but introduces an explicit external dependency on an `ffmpeg` binary (distinct from the FFmpeg libraries already used internally by Qt) that needs bundling into the PyInstaller package.

**Decision made:** option 2 is adopted as the primary approach, not as a fallback. Rationale: the hang documented in Phase 0 is a Qt Multimedia backend behaviour with no long-term stability guarantee (future Qt versions, untested repeated use) — a risk that is fundamentally outside our control. By contrast, a dependency on an external `ffmpeg` binary is a known, bounded, and fully controllable risk (explicit bundling, testable once and for all). Between an uncertain and recurring risk and a certain but manageable one, the latter is the safer choice for a feature that runs in a loop across potentially dozens of files.

**Practical consequence:**
- The `ffmpeg` binary must be explicitly bundled into the PyInstaller executable (not merely assumed to be present on the user's machine), so as not to break the standalone-executable promise established in V1 (US-060)
- `core/thumbnail_generator.py` invokes `ffmpeg` via `subprocess.run()`, with explicit handling of extraction failures (corrupted file, timeout) — graceful degradation to a generic icon rather than a crash
- The load test (20+ files) remains relevant but changes in nature: it no longer verifies the absence of a Qt-side hang, but instead the robustness and performance of repeated subprocess invocation (cumulative execution time, handling of zombie processes on failure)

**Components involved:** new `core/thumbnail_generator.py`, an on-disk thumbnail cache (`~/Library/Caches/MediaPlayer/thumbnails/`) to avoid regenerating thumbnails on every launch.

### 3.6 F17 — External subtitles

**Description:** load an `.srt` file associated with a video and display the subtitles as an overlay.

**Major point of caution:** QtMultimedia (`QMediaPlayer`) has no built-in rendering for manually loaded external `.srt` subtitle files (unlike subtitle tracks embedded in some containers, which are handled differently). This requires:
1. Parsing the `.srt` file manually (a simple format, but watch for encoding — UTF-8 vs Latin-1 depending on the file's origin)
2. Displaying the text matching the current playback position in a `QLabel` overlaid on the `QVideoWidget` (absolute positioning or a dedicated layout)
3. Synchronising the display with the player's `positionChanged` signal, with a tolerance of a few hundred milliseconds

**Components involved:** new `core/subtitle_parser.py` (`.srt` parsing), new `ui/subtitle_overlay.py` (overlay widget)

### 3.7 F18 — Playback speed

**Description:** adjust playback speed from 0.5x to 2x.

**Components involved:** `core/player_engine.py` — add a `set_playback_rate(rate: float)` method delegating directly to `QMediaPlayer.setPlaybackRate()`. This is the simplest V2 feature, purely additive, with no identified regression risk.

### 3.8 F19 — Mini-mode

**Description:** switch to a compact, always-on-top window showing only the video and minimal controls.

**Components involved:** new `ui/mini_mode_window.py`, sharing the same `PlayerViewModel` as `MainWindow` (no new `PlayerEngine` instance — a single active player, just a different view onto it).

**Architectural point of attention:** this is the most direct stress test of the V1 PRD's MVVM pattern — if both `MainWindow` and `MiniModeWindow` can subscribe to the same `PlayerViewModel` without duplicating state or drifting out of sync, the V1 architecture is validated retrospectively. If this proves difficult, it is a signal that the V1 ViewModel has accumulated logic that should have stayed in `core/`.

This is worth stating slightly more forcefully than the French version does: if F19 turns out to require duplicating state between the two windows, that is not a V2-specific problem to patch around locally — it is evidence of a V1 architectural debt that should be fixed at the `PlayerViewModel` level before F19 is considered complete, even if that means briefly stepping back into "V1 code" during V2 development.

### 3.9 F20 — Fullscreen video

**Description:** toggle the video area (or the whole window) into fullscreen, via a double-click on the video or a keyboard shortcut, exiting via Escape or a second double-click.

**Components involved:** `ui/main_window.py` (or `ui/video_widget.py`, depending on whether fullscreen covers the entire window or just the video area — recommendation: the whole window, via `MainWindow.showFullScreen()`/`showNormal()`, which is simpler to keep consistent with the existing controls than detaching the video area into a separate window).

**Points of attention:**
- Recommended interaction: double-click on `QVideoWidget` to enter, `Escape` to exit — consistent with the conventions established by most video players
- **Deliberately minimal scope for V2**: basic fullscreen does not involve automatically hiding the controls after mouse inactivity. That refinement (a timer plus `mouseMoveEvent` handling to show the controls on mouse movement and hide them again after a few seconds of inactivity) is deferred to V3 unless judged a priority — it adds UX complexity without changing the core functionality
- Check the interaction with mini-mode (F19): fullscreen should be disabled, or clearly redefined, while mini-mode is active, to avoid an ambiguous state between the two windows

**No impact on `core/`** — this feature is purely a presentation concern, with no regression risk to the business logic tested in V1.

This is arguably the cleanest feature in the whole V2 scope from a risk standpoint, and it is worth naming that explicitly rather than letting it blend into the rest of the list: F20 touches no `core/` file, requires no new test infrastructure, and has essentially no failure mode beyond a UI glitch. If time pressure forces a cut somewhere in Phase 8, this is not where it should come from.

---

## 4. New architecture components (overview)

```
media_player/
├── core/
│   ├── playlist_persistence.py   # NEW (F12) — playlist.json
│   ├── settings_manager.py       # NEW (F15) — settings.json, separate from playlist.json
│   ├── shuffle_strategy.py       # NEW if needed (F14)
│   ├── thumbnail_generator.py    # NEW (F16) — invokes ffmpeg as a subprocess
│   ├── subtitle_parser.py        # NEW (F17)
│   ├── models.py                 # MODIFIED — add RepeatMode enum (F13)
│   ├── playlist_manager.py       # MODIFIED — repeat_mode, shuffle (F13, F14)
│   └── player_engine.py          # MODIFIED — set_playback_rate (F18)
├── ui/
│   ├── theme_manager.py          # NEW (F15)
│   ├── mini_mode_window.py       # NEW (F19)
│   ├── subtitle_overlay.py       # NEW (F17)
│   ├── playlist_widget.py        # MODIFIED — thumbnail display (F16)
│   └── video_widget.py           # MODIFIED — overlay integration (F17)
└── tests/
    ├── test_playlist_persistence.py   # NEW
    ├── test_thumbnail_generator.py    # NEW
    ├── test_subtitle_parser.py        # NEW
    └── test_playlist_manager.py       # EXTENDED (F13, F14), with no regression on existing V1 tests
```

---

## 5. Non-functional requirements (V2)

| Category | Requirement |
|---|---|
| Non-regression | 100% of existing V1 tests continue to pass with no changes to their assertions (only new tests are added) |
| Performance | Thumbnail generation must not block the UI (asynchronous or background processing, e.g. `QThread` or `QThreadPool`) |
| Robustness | A malformed `.srt` file must not prevent video playback (graceful degradation: video plays without subtitles, plus a discreet message) |
| Maintainability | Test coverage >= 70% maintained across the whole of `core/`, including new files |
| Compatibility | All V2 features must work on macOS (the platform validated in V1); this V2 does not extend platform scope |

---

## 6. Development plan

| Phase | Content | Expected output |
|---|---|---|
| Phase 7 — Persistence & settings | F12, `app_settings.py` foundation | Playlist and preferences survive a restart |
| Phase 8 — Speed, fullscreen & theme | F18, F20, F15 | Low-risk, additive features, delivered quickly |
| Phase 9 — Repeat & shuffle | F13, F14 | Extended `PlaylistManager`, non-regression validated by existing V1 tests |
| Phase 10 — Mini-mode | F19 | Cross-validation of the V1 MVVM architecture |
| Phase 11 — Thumbnails | F16 (`ffmpeg` subprocess extraction) | Load test on the robustness/performance of repeated subprocess invocation; `ffmpeg` binary packaging validated |
| Phase 12 — Subtitles | F17 | The final, most complex phase; can be deferred to a V3 if the V2 time budget is exceeded |

**Note:** unlike the V1 breakdown, where each phase was strictly sequential, V2's Phases 7 through 10 are largely independent of one another and can be reordered according to your availability (Saturdays) with no risk of a blocking dependency. Only Phases 11 and 12 must remain at the end, for the technical-risk reasons detailed in sections 3.5 and 3.6.

---

## 7. Acceptance criteria (V2 Definition of Done)

V2 is considered complete when:

1. The playlist and preferences (theme, last volume level) are restored after restarting the application
2. All three repeat modes work, as does shuffle mode, with no regression in the default V1 behaviour
3. The dark/light theme can be toggled and persists across sessions
4. Playback speed is adjustable from 0.5x to 2x without major audio/video artefacts
5. Fullscreen can be toggled via double-click and a keyboard shortcut, with no state conflict against mini-mode
6. Mini-mode reflects the main player's playback state in real time, in both directions (controlling from mini-mode affects the main window, and vice versa)
7. Thumbnails display in the playlist for at least 95% of the video formats supported in V1, with no reproducible hang across a load test of 20+ files
8. `.srt` subtitles display in sync with playback, with graceful degradation on a malformed file
9. 100% of existing V1 tests still pass, in addition to the new V2 tests
10. Overall test coverage on `core/` remains >= 70%

---

## 8. Identified risks

| Risk | Impact | Mitigation |
|---|---|---|
| Recurrence of the `QVideoSink`/`stop()` hang under repeated thumbnail generation | Eliminated | Option ruled out (see section 3.5) — `ffmpeg` subprocess extraction adopted from the outset, avoiding any dependency on the `QMediaPlayer` pipeline |
| Silent regression in `PlaylistManager.next()/previous()` (F13/F14) | High | Existing V1 test assertions must never be modified; any behavioural change goes through a new, backward-compatible default-valued parameter |
| Increased size of the packaged executable (thumbnails, subtitles, themes) | Medium | Measure the executable's size before/after each feature, and document in the README if it exceeds a reasonable threshold |
| Dependency on an external `ffmpeg` binary for F16 | Medium | Explicitly bundle the binary in the PyInstaller packaging (extending US-060) rather than assuming system-level presence; document this dependency as distinct from the FFmpeg libraries used internally by Qt |
| Scope creep into an unplanned V3 | Low | Phases 11/12 are explicitly flagged as deferrable; no new feature outside those listed in section 2 should be added without a formal revision of this PRD |

---

## 9. Decisions made

1. **Settings mechanism:** two separate JSON files — `playlist.json` (F12) and `settings.json` (F15) — rather than a single file. This isolates the two responsibilities and prevents corruption or a schema change in one from affecting the other.
2. **F16 (thumbnails):** `ffmpeg` subprocess extraction is adopted as the primary approach (not as a fallback). The hang risk on the `QVideoSink`/Qt Multimedia backend side, documented in Phase 0, is an uncontrolled risk that is better avoided entirely than tested in the hope it won't recur at scale. A dependency on a bundled `ffmpeg` binary is a known, bounded risk, judged safer.
3. **F17 (subtitles):** stays within V2 scope (Phase 12); no ring-fencing into V3 for now. This decision is not set in stone — if time runs short towards the end of V2, section 8 (risks) already accounts for that possibility of deferral.
