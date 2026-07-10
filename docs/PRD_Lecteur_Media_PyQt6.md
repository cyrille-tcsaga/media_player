# PRD — Lecteur Audio/Vidéo PyQt6 + QtMultimedia

**Auteur :** Cyrille (CodexSoft)
**Statut :** Draft V1
**Date :** Juillet 2026

---

## 1. Contexte et objectif

Projet personnel/exploratoire visant à construire un lecteur audio/vidéo desktop en Python, en s'appuyant sur PyQt6 et le module QtMultimedia. L'objectif n'est pas de concurrencer VLC, mais de produire un projet propre, testable, avec une architecture claire, qui puisse servir de :

- Portfolio technique (démonstration de compétences Python/Qt hors de l'écosystème habituel Spring/Vue/Flutter)
- Base réutilisable pour d'éventuels besoins futurs (lecteur intégré à un produit CodexSoft, par exemple un module de prévisualisation média)
- Terrain d'apprentissage sur QtMultimedia, la gestion d'état UI, et les patterns MVC/MVVM en environnement desktop

**Non-objectifs (explicitement hors scope V1) :**
- Streaming réseau (HTTP/RTSP)
- Conversion/transcodage de fichiers
- Édition vidéo
- Support plugin/extension tiers
- Synchronisation cloud ou bibliothèque multi-appareils

---

## 2. Public cible

- Utilisateur unique : Cyrille lui-même, usage personnel/démo
- Cas d'usage secondaire : démonstration publique sur LinkedIn/Facebook dans le cadre de son positionnement de "builder" partageant son apprentissage technique

---

## 3. Périmètre fonctionnel

### 3.1 MVP (V1) — must-have

| # | Fonctionnalité | Détail |
|---|---|---|
| F1 | Ouverture de fichier | Dialogue natif de sélection de fichier (audio + vidéo) |
| F2 | Lecture / Pause | Bouton + raccourci clavier (Espace) |
| F3 | Stop | Retour à l'état initial (position 0, lecture arrêtée) |
| F4 | Barre de progression | Slider cliquable + draggable, mise à jour en temps réel, affichage temps écoulé / durée totale |
| F5 | Contrôle du volume | Slider 0-100, mute/unmute |
| F6 | Affichage vidéo | Zone de rendu vidéo (QVideoWidget), redimensionnable, conservant le ratio d'aspect |
| F7 | Playlist simple | Liste de fichiers ajoutés, sélection pour lecture, suppression d'un élément |
| F8 | Navigation playlist | Piste suivante / précédente |
| F9 | Drag & drop | Glisser un ou plusieurs fichiers dans la fenêtre pour les ajouter à la playlist |
| F10 | Gestion des erreurs | Message utilisateur clair si le fichier est corrompu, codec non supporté, ou introuvable |
| F11 | Raccourcis clavier | Espace (play/pause), flèches gauche/droite (seek ±5s), flèches haut/bas (volume ±5%) |

### 3.2 V2 — nice-to-have (post-MVP)

| # | Fonctionnalité | Détail |
|---|---|---|
| F12 | Persistance playlist | Sauvegarde/rechargement au format JSON local |
| F13 | Mode répétition | Aucune / une piste / toute la playlist |
| F14 | Mode aléatoire | Lecture shuffle |
| F15 | Thème sombre/clair | Toggle UI |
| F16 | Miniatures vidéo | Génération de vignettes pour la playlist |
| F17 | Sous-titres | Chargement de fichiers .srt externes |
| F18 | Vitesse de lecture | 0.5x à 2x |
| F19 | Mini-mode | Fenêtre compacte type "always on top" |

### 3.3 Hors scope définitif

- Support DRM (Netflix, Widevine, etc.)
- Égaliseur audio avancé
- Enregistrement/capture

---

## 4. Architecture technique

### 4.1 Stack

| Composant | Choix | Justification |
|---|---|---|
| Langage | Python 3.11+ | Cohérence avec l'écosystème dispo, typing moderne |
| Framework UI | PyQt6 | Bindings Qt6 les plus stables, licence GPL acceptable pour projet perso/portfolio |
| Lecture média | QtMultimedia (`QMediaPlayer`, `QAudioOutput`, `QVideoWidget`) | Natif Qt, pas de dépendance externe lourde |
| Gestion de dépendances | `venv` + `requirements.txt` | Simplicité, suffisant pour un projet mono-développeur (décision actée, cf. section 10) |
| Tests | `pytest` + `pytest-qt` | Tests unitaires et tests d'intégration UI |
| Packaging | `PyInstaller` | Distribution en exécutable standalone (Windows/macOS/Linux) |

### 4.2 Pattern architectural : MVVM allégé

Cyrille ayant l'habitude de Clean Architecture (Spring Boot) et Riverpod (Flutter), on reproduit un séparation claire des responsabilités plutôt qu'un unique fichier monolithique `main.py` :

```
media_player/
├── main.py                  # Point d'entrée, bootstrap Qt Application
├── core/
│   ├── player_engine.py     # Wrapper autour de QMediaPlayer (logique métier pure)
│   ├── playlist_manager.py  # Gestion de la playlist (ajout/suppression/navigation)
│   └── models.py            # Dataclasses : MediaItem, PlaybackState, etc.
├── ui/
│   ├── main_window.py       # QMainWindow, assemble les widgets
│   ├── controls_widget.py   # Boutons play/pause/stop/volume
│   ├── progress_widget.py   # Slider de progression + labels temps
│   ├── playlist_widget.py   # QListWidget custom pour la playlist
│   └── video_widget.py      # Wrapper QVideoWidget avec gestion ratio
├── viewmodels/
│   └── player_viewmodel.py  # Fait le lien entre core/ et ui/, expose des signaux Qt
├── utils/
│   └── formatters.py        # Formatage durée (ms -> mm:ss), etc.
└── tests/
    ├── test_player_engine.py
    ├── test_playlist_manager.py
    └── test_ui_integration.py
```

**Principe directeur :** `core/` ne doit jamais importer quoi que ce soit de `PyQt6.QtWidgets`. Seul `ui/` connaît les widgets. `viewmodels/` fait le pont via les signaux/slots Qt (`pyqtSignal`), ce qui permet de tester `core/` sans instancier la moindre fenêtre.

### 4.3 Flux de données (exemple : play/pause)

1. L'utilisateur clique sur le bouton play dans `controls_widget.py`
2. Le widget émet un signal `play_requested`
3. `player_viewmodel.py` reçoit le signal, appelle `player_engine.play()`
4. `player_engine.py` délègue à `QMediaPlayer.play()`
5. `QMediaPlayer` émet `playbackStateChanged`
6. Le ViewModel écoute ce signal et met à jour son propre état exposé
7. `main_window.py` réagit et met à jour l'icône du bouton (play -> pause)

---

## 5. Exigences non fonctionnelles

| Catégorie | Exigence |
|---|---|
| Performance | Latence d'ouverture de fichier < 1s pour fichiers locaux < 500 Mo |
| Compatibilité | Windows 10+, Ubuntu 22.04+, macOS 13+ (au minimum test sur l'environnement principal de dev de Cyrille) |
| Robustesse | Aucun crash sur fichier corrompu ou format non supporté ; message d'erreur explicite systématique |
| Maintenabilité | Couverture de tests unitaires >= 70% sur `core/` |
| Accessibilité | Navigation clavier complète des contrôles principaux |

---

## 6. Format des fichiers supportés (V1)

Dépendant du backend FFmpeg embarqué par Qt6 Multimedia sur la plateforme cible. À valider empiriquement en tout début de dev (spike technique, cf. section 8) :

- Vidéo : MP4 (H.264/H.265), WebM, MKV (support variable selon OS)
- Audio : MP3, WAV, OGG, FLAC (support variable selon OS)

**Point de vigilance identifié :** sur Windows, Qt6 Multimedia s'appuie sur le backend natif (Media Foundation) et non FFmpeg par défaut selon la version de Qt — cela peut limiter certains formats (notamment MKV/H.265 sans codecs additionnels installés). Ce point doit être vérifié tôt (spike) pour éviter une surprise en fin de développement.

---

## 7. Plan de développement (approche par incréments)

| Phase | Contenu | Sortie attendue |
|---|---|---|
| Phase 0 — Spike technique | Valider QMediaPlayer + QVideoWidget sur un fichier MP4 et un MP3 simple, sans UI soignée | Preuve de fonctionnement, liste des formats réellement supportés sur ta machine |
| Phase 1 — Squelette architecture | Mettre en place la structure de dossiers, les classes vides, les tests de base | Structure de projet committée, CI basique (lint + tests) |
| Phase 2 — Lecture basique | F1, F2, F3, F6 | Lire play/pause/stop un fichier vidéo unique |
| Phase 3 — Contrôles avancés | F4, F5, F11 | Barre de progression fonctionnelle, volume, raccourcis clavier |
| Phase 4 — Playlist | F7, F8, F9 | Playlist complète avec drag & drop |
| Phase 5 — Robustesse | F10 + tests + gestion des cas limites | Gestion d'erreurs complète, couverture de tests cible atteinte |
| Phase 6 — Packaging | PyInstaller, tests sur exécutable final | Exécutable distribuable |

**Remarque sur ton emploi du temps :** vu que tu structures tes projets perso sur les samedis (et éventuellement mercredis/jeudis selon ta charge actuelle avec la stack microservices), ce découpage en 6 phases permet de traiter chaque phase sur une ou deux sessions de travail, avec un état fonctionnel testable à la fin de chaque phase — utile si tu dois interrompre le projet plusieurs semaines.

---

## 8. Critères d'acceptation (Definition of Done du MVP)

Le MVP est considéré complet quand :

1. Un utilisateur peut ouvrir un fichier vidéo MP4 et un fichier audio MP3, les lire, les mettre en pause, les stopper
2. La barre de progression reflète fidèlement la position de lecture et permet de seek par clic/drag
3. Le volume est ajustable et le mute fonctionne
4. Une playlist d'au moins 5 fichiers peut être constituée par drag & drop, avec navigation suivant/précédent
5. Un fichier corrompu ou dans un format non supporté génère un message d'erreur clair, sans crash de l'application
6. La couverture de tests sur `core/` atteint au moins 70%
7. L'application se lance en moins de 2 secondes sur la machine de dev

---

## 9. Risques identifiés

| Risque | Impact | Mitigation |
|---|---|---|
| Support codec incomplet selon OS | Élevé | Spike technique dès Phase 0, documenter les formats validés |
| Complexité sous-estimée de la synchronisation UI/état de lecture | Moyen | Architecture MVVM stricte, tests unitaires sur le ViewModel |
| PyInstaller et QtMultimedia (DLLs manquantes à l'empaquetage) | Moyen | Tester le packaging tôt (Phase 6 anticipée partiellement en Phase 2) plutôt qu'en toute fin de projet |
| Dérive de scope (ajout de fonctionnalités V2 pendant le MVP) | Moyen | Ce PRD fait foi ; toute fonctionnalité V2 est reportée sans négociation pendant le développement du MVP |

---

## 10. Décisions actées

| Question | Décision |
|---|---|
| Plateforme de dev principale | macOS |
| Gestionnaire de dépendances | `venv` + `requirements.txt` |
| Visibilité du dépôt | Public (GitHub) |

**Implications de ces décisions :**

- **macOS** : bonne nouvelle par rapport au point de vigilance de la section 6. Depuis Qt 6.5, le backend FFmpeg est le backend par défaut sur macOS (comme sur Windows et Linux), avec un backend natif `darwin` disponible en repli via la variable d'environnement `QT_MEDIA_BACKEND`. Le risque de support codec incomplet est donc moindre que redouté initialement, à condition de vérifier la version de Qt installée (le spike Phase 0 doit explicitement afficher/logguer le backend actif au démarrage, pour éviter une bascule silencieuse vers le backend natif en cas de bibliothèque manquante).
- **`venv` + `requirements.txt`** : choix simple et suffisant pour un projet mono-développeur sans matrice de compatibilité complexe. À documenter dans le README avec la version Python exacte utilisée (recommandé : figer via `pip freeze > requirements.txt` après validation de chaque phase, pas uniquement en fin de projet).
- **Dépôt public** : lève l'ambiguïté sur la licence PyQt6 (GPLv3) — un dépôt open source est compatible avec cette licence sans complication puisque le code source est de toute façon public. Le point de vigilance mentionné plus haut (bascule vers PySide6 en cas de réutilisation commerciale fermée chez CodexSoft) reste valable, mais devient un non-sujet tant que ce projet reste ce qu'il est : un portfolio public.

**Conséquence concrète sur la Phase 0 et la Phase 1 :**

- Phase 0 : ajouter explicitement un test de détection du backend actif (logguer la variable d'environnement `QT_MEDIA_BACKEND` et le résultat empirique de lecture d'un fichier MKV/H.265)
- Phase 1 : le README doit dès le premier commit préciser la version de Python, la commande de création du `venv`, et la licence du dépôt (GPLv3, cohérente avec PyQt6)

---
---

# PRD (English) — Audio/Video Player, PyQt6 + QtMultimedia

**Author:** Cyrille (CodexSoft)
**Status:** Draft V1
**Date:** July 2026

---

## 1. Background and objective

This is a personal/exploratory project aimed at building a desktop audio/video player in Python, built on PyQt6 and the QtMultimedia module. The goal is not to compete with VLC, but to produce a clean, testable project with a clear architecture that can serve as:

- A technical portfolio piece (demonstrating Python/Qt skills outside the usual Spring/Vue/Flutter ecosystem)
- A reusable foundation for potential future needs (a media player embedded in a CodexSoft product, for example a media preview module)
- A learning ground for QtMultimedia, UI state management, and MVC/MVVM patterns in a desktop environment

**Non-goals (explicitly out of scope for V1):**
- Network streaming (HTTP/RTSP)
- File conversion/transcoding
- Video editing
- Third-party plugin/extension support
- Cloud synchronisation or multi-device library

This is a slightly broader restatement of scope than the French version's non-objectives, to remove any ambiguity before development starts: the intent is a **local, single-user, single-machine** player. Any requirement that implies a server component, a second device, or a network protocol should be treated as out of scope by default unless this PRD is explicitly revised.

---

## 2. Target audience

- Single user: Cyrille himself, for personal use and demonstration purposes
- Secondary use case: public demonstration on LinkedIn/Facebook as part of his "builder" positioning, sharing genuine technical learning

The secondary use case has a mild implication worth flagging explicitly: since the project may be shown publicly, the codebase's readability and commit history arguably matter almost as much as the shipped feature set. This is worth bearing in mind when deciding how granular to make commits during each development phase.

---

## 3. Functional scope

### 3.1 MVP (V1) — must-have

| # | Feature | Detail |
|---|---|---|
| F1 | Open file | Native file selection dialog (audio + video) |
| F2 | Play / Pause | Button + keyboard shortcut (Space) |
| F3 | Stop | Return to initial state (position 0, playback stopped) |
| F4 | Progress bar | Clickable and draggable slider, updated in real time, showing elapsed time / total duration |
| F5 | Volume control | 0–100 slider, mute/unmute |
| F6 | Video display | Video rendering area (QVideoWidget), resizable, preserving aspect ratio |
| F7 | Simple playlist | List of added files, selectable for playback, item removal |
| F8 | Playlist navigation | Next / previous track |
| F9 | Drag & drop | Drag one or more files into the window to add them to the playlist |
| F10 | Error handling | Clear user-facing message if the file is corrupt, the codec is unsupported, or the file cannot be found |
| F11 | Keyboard shortcuts | Space (play/pause), left/right arrows (seek ±5s), up/down arrows (volume ±5%) |

### 3.2 V2 — nice-to-have (post-MVP)

| # | Feature | Detail |
|---|---|---|
| F12 | Playlist persistence | Save/reload as local JSON |
| F13 | Repeat mode | None / single track / whole playlist |
| F14 | Shuffle mode | Randomised playback |
| F15 | Dark/light theme | UI toggle |
| F16 | Video thumbnails | Thumbnail generation for the playlist |
| F17 | Subtitles | Loading of external .srt files |
| F18 | Playback speed | 0.5x to 2x |
| F19 | Mini-mode | Compact "always on top" window |

### 3.3 Permanently out of scope

- DRM support (Netflix, Widevine, etc.)
- Advanced audio equaliser
- Recording/capture

---

## 4. Technical architecture

### 4.1 Stack

| Component | Choice | Justification |
|---|---|---|
| Language | Python 3.11+ | Consistency with the available ecosystem, modern typing support |
| UI framework | PyQt6 | Most stable Qt6 bindings; GPL licensing is acceptable for a personal/portfolio project |
| Media playback | QtMultimedia (`QMediaPlayer`, `QAudioOutput`, `QVideoWidget`) | Native to Qt, no heavy external dependency |
| Dependency management | `venv` + `requirements.txt` | Simplicity, sufficient for a single-developer project (decision made, see section 10) |
| Testing | `pytest` + `pytest-qt` | Unit tests and UI integration tests |
| Packaging | `PyInstaller` | Standalone executable distribution (Windows/macOS/Linux) |

A note worth making explicit here, since the French version leaves it implicit: choosing PyQt6 over PySide6 is a licensing decision, not just a technical one. PyQt6 is GPLv3 (or commercial), which is fine for a personal/portfolio project that is never sold as a closed-source product, but would become a real constraint the moment this codebase is repurposed inside a commercial CodexSoft product. If that repurposing is ever considered, PySide6 (LGPL) should be re-evaluated at that point rather than assumed away.

### 4.2 Architectural pattern: lightweight MVVM

Since Cyrille is used to Clean Architecture (Spring Boot) and Riverpod (Flutter), the same clear separation of responsibilities is reproduced here, rather than a single monolithic `main.py` file:

```
media_player/
├── main.py                  # Entry point, bootstraps the Qt Application
├── core/
│   ├── player_engine.py     # Wrapper around QMediaPlayer (pure business logic)
│   ├── playlist_manager.py  # Playlist management (add/remove/navigate)
│   └── models.py            # Dataclasses: MediaItem, PlaybackState, etc.
├── ui/
│   ├── main_window.py       # QMainWindow, assembles the widgets
│   ├── controls_widget.py   # Play/pause/stop/volume buttons
│   ├── progress_widget.py   # Progress slider + time labels
│   ├── playlist_widget.py   # Custom QListWidget for the playlist
│   └── video_widget.py      # QVideoWidget wrapper with aspect ratio handling
├── viewmodels/
│   └── player_viewmodel.py  # Bridges core/ and ui/, exposes Qt signals
├── utils/
│   └── formatters.py        # Duration formatting (ms -> mm:ss), etc.
└── tests/
    ├── test_player_engine.py
    ├── test_playlist_manager.py
    └── test_ui_integration.py
```

**Guiding principle:** `core/` must never import anything from `PyQt6.QtWidgets`. Only `ui/` is aware of widgets. `viewmodels/` bridges the two via Qt signals/slots (`pyqtSignal`), which allows `core/` to be tested without instantiating a single window.

### 4.3 Data flow (example: play/pause)

1. The user clicks the play button in `controls_widget.py`
2. The widget emits a `play_requested` signal
3. `player_viewmodel.py` receives the signal and calls `player_engine.play()`
4. `player_engine.py` delegates to `QMediaPlayer.play()`
5. `QMediaPlayer` emits `playbackStateChanged`
6. The ViewModel listens for this signal and updates its own exposed state
7. `main_window.py` reacts and updates the button icon (play -> pause)

---

## 5. Non-functional requirements

| Category | Requirement |
|---|---|
| Performance | File-opening latency < 1s for local files under 500 MB |
| Compatibility | Windows 10+, Ubuntu 22.04+, macOS 13+ (at minimum, testing on Cyrille's primary development environment) |
| Robustness | No crash on corrupted files or unsupported formats; a clear error message every time |
| Maintainability | Unit test coverage >= 70% on `core/` |
| Accessibility | Full keyboard navigation of the main controls |

---

## 6. Supported file formats (V1)

Dependent on the FFmpeg backend embedded by Qt6 Multimedia on the target platform. This must be validated empirically right at the start of development (technical spike, see section 8):

- Video: MP4 (H.264/H.265), WebM, MKV (support varies by OS)
- Audio: MP3, WAV, OGG, FLAC (support varies by OS)

**Identified point of caution:** on Windows, Qt6 Multimedia relies on the native backend (Media Foundation) rather than FFmpeg by default, depending on the Qt version — this can limit certain formats (notably MKV/H.265 without additional codecs installed). This must be checked early (spike) to avoid an unpleasant surprise late in development.

To go one step further than the French version on this point: it would be worth deciding, during the Phase 0 spike, on an explicit fallback policy for unsupported formats — for instance, whether the application should silently reject a file with an error message (current F10 scope) or eventually offer a "convert with FFmpeg first" path. Given the project's stated non-goals, the former is the correct default, but it is worth stating that decision explicitly rather than discovering it by omission.

---

## 7. Development plan (incremental approach)

| Phase | Content | Expected output |
|---|---|---|
| Phase 0 — Technical spike | Validate QMediaPlayer + QVideoWidget on a simple MP4 file and an MP3 file, without a polished UI | Proof of functionality, list of formats actually supported on your machine |
| Phase 1 — Architecture skeleton | Set up the folder structure, empty classes, basic tests | Committed project structure, basic CI (lint + tests) |
| Phase 2 — Basic playback | F1, F2, F3, F6 | Play/pause/stop a single video file |
| Phase 3 — Advanced controls | F4, F5, F11 | Working progress bar, volume, keyboard shortcuts |
| Phase 4 — Playlist | F7, F8, F9 | Full playlist with drag & drop |
| Phase 5 — Robustness | F10 + tests + edge case handling | Complete error handling, target test coverage reached |
| Phase 6 — Packaging | PyInstaller, tests on the final executable | Distributable executable |

**Note on your schedule:** given that you structure personal projects around Saturdays (and possibly Wednesdays/Thursdays depending on your current workload with the microservices stack), this six-phase breakdown allows each phase to be handled in one or two work sessions, with a testable working state at the end of each phase — useful if the project needs to be paused for several weeks.

One addition relative to the French version: it is worth deciding now, rather than mid-project, what "done" means for Phase 6 specifically — a signed executable is a materially different deliverable from an unsigned one flagged by Windows SmartScreen or macOS Gatekeeper, and code-signing on macOS in particular requires an Apple Developer account and adds real friction. If the executable is only ever meant to run on your own machine, that friction can reasonably be skipped; if it is meant to be shared as a portfolio artefact, it should be planned for.

---

## 8. Acceptance criteria (MVP Definition of Done)

The MVP is considered complete when:

1. A user can open an MP4 video file and an MP3 audio file, play them, pause them, and stop them
2. The progress bar accurately reflects the playback position and allows seeking via click/drag
3. Volume is adjustable and mute works
4. A playlist of at least 5 files can be built via drag & drop, with next/previous navigation
5. A corrupted file or one in an unsupported format produces a clear error message, without crashing the application
6. Test coverage on `core/` reaches at least 70%
7. The application launches in under 2 seconds on the development machine

---

## 9. Identified risks

| Risk | Impact | Mitigation |
|---|---|---|
| Incomplete codec support depending on OS | High | Technical spike from Phase 0, document validated formats |
| Underestimated complexity of UI/playback-state synchronisation | Medium | Strict MVVM architecture, unit tests on the ViewModel |
| PyInstaller and QtMultimedia (missing DLLs at packaging time) | Medium | Test packaging early (partially anticipate Phase 6 during Phase 2) rather than only at the very end of the project |
| Scope creep (adding V2 features during MVP work) | Medium | This PRD is authoritative; any V2 feature is deferred without negotiation during MVP development |

A risk worth adding that does not appear in the French version: **solo-project attrition risk.** Given that this competes for time with the salaried role at Makiti Group, the freelance pipeline, and the microservices curriculum, the six-phase structure is only useful as a mitigation if each phase genuinely ends in a working, demoable state — a partially-finished Phase 3 is much easier to abandon than a finished Phase 2. It may be worth treating "does this phase produce something demoable" as an informal exit condition for each phase, independent of the formal acceptance criteria in section 8.

---

## 10. Decisions made

| Question | Decision |
|---|---|
| Primary development platform | macOS |
| Dependency manager | `venv` + `requirements.txt` |
| Repository visibility | Public (GitHub) |

**Implications of these decisions:**

- **macOS**: good news relative to the point of caution raised in section 6. Since Qt 6.5, the FFmpeg backend has been the default backend on macOS (as on Windows and Linux), with a native `darwin` backend available as a fallback via the `QT_MEDIA_BACKEND` environment variable. The risk of incomplete codec support is therefore lower than initially feared, provided the installed Qt version is verified (the Phase 0 spike should explicitly display/log the active backend at startup, to avoid a silent fallback to the native backend if a library is missing).
- **`venv` + `requirements.txt`**: a simple choice, sufficient for a single-developer project without a complex compatibility matrix. This should be documented in the README with the exact Python version used (recommended: freeze via `pip freeze > requirements.txt` after each phase is validated, not only at the end of the project).
- **Public repository**: this resolves the earlier ambiguity around the PyQt6 licence (GPLv3) — an open source repository is straightforwardly compatible with this licence, since the source code is public regardless. The earlier point of caution (switching to PySide6 if the project is ever reused in a closed-source commercial context at CodexSoft) still stands as a general principle, but becomes a non-issue for as long as this project remains what it is: a public portfolio piece.

**Concrete consequence for Phase 0 and Phase 1:**

- Phase 0: explicitly add a check for the active backend (log the `QT_MEDIA_BACKEND` environment variable and the empirical result of playing an MKV/H.265 file)
- Phase 1: the README must state, from the first commit, the Python version used, the `venv` creation command, and the repository's licence (GPLv3, consistent with PyQt6)
