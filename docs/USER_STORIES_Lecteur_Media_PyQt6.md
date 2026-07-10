# User Stories — Lecteur Audio/Vidéo PyQt6 + QtMultimedia

**Document compagnon du PRD** (`PRD_Lecteur_Media_PyQt6.md`)
**Usage :** ce fichier est conçu pour être exécuté séquentiellement par Claude Code, story par story, dans l'ordre indiqué. Chaque story est autonome, testable, et référence l'architecture définie dans le PRD (section 4.2).

**Convention d'ID :** `US-PPNN` où `PP` = numéro de phase (00 à 06), `NN` = numéro de story dans la phase.

**Règle pour Claude Code :** ne pas passer à la story suivante tant que les critères d'acceptation de la story courante ne sont pas tous vérifiés (tests passants inclus). Commit atomique par story recommandé (message de commit = ID + titre de la story).

---

## Phase 0 — Spike technique

### US-000 — Initialiser l'environnement de développement

**En tant que** développeur, **je veux** un environnement Python isolé et reproductible, **afin de** garantir que le projet fonctionne de manière identique à chaque relance.

**Critères d'acceptation :**
- Un `venv` est créé à la racine du projet (`python3 -m venv venv`)
- Un fichier `requirements.txt` existe avec au minimum `PyQt6` (dernière version stable 6.x)
- Un fichier `.gitignore` exclut `venv/`, `__pycache__/`, `*.pyc`
- Un fichier `README.md` minimal précise : version Python utilisée, commande d'activation du venv, commande d'installation des dépendances

**Fichiers concernés :** `requirements.txt`, `.gitignore`, `README.md`

**Dépendances :** aucune

**Notes pour Claude Code :** ne pas encore ajouter `pytest`/`pytest-qt` ici — ce sera fait en US-013. Se limiter au strict nécessaire pour faire tourner PyQt6.

---

### US-001 — Valider la lecture vidéo basique

**En tant que** développeur, **je veux** un script minimal prouvant que `QMediaPlayer` + `QVideoWidget` peuvent lire un fichier MP4 local, **afin de** valider que la stack technique fonctionne avant d'investir dans l'architecture complète.

**Critères d'acceptation :**
- Un script `spike/video_spike.py` ouvre une fenêtre Qt avec un `QVideoWidget`
- Le script lit un fichier MP4 passé en argument de ligne de commande (`python spike/video_spike.py chemin/vers/fichier.mp4`)
- La vidéo se lance automatiquement à l'ouverture et l'image s'affiche correctement
- Le script logge dans la console le backend Qt Multimedia actif au démarrage (variable d'environnement `QT_MEDIA_BACKEND` si définie, sinon mention explicite "backend par défaut")

**Fichiers concernés :** `spike/video_spike.py`

**Dépendances :** US-000

**Notes pour Claude Code :** ce code est jetable, pas de tests unitaires exigés ici, pas de respect de l'architecture MVVM — c'est un script exploratoire isolé dans `spike/`, qui ne doit pas être importé par le reste du projet.

---

### US-002 — Valider la lecture audio basique et le détecteur de backend

**En tant que** développeur, **je veux** valider la lecture d'un fichier MP3 et documenter le backend réellement utilisé sur ma machine macOS, **afin de** lever le risque identifié en section 6/9 du PRD avant la Phase 2.

**Critères d'acceptation :**
- Un script `spike/audio_spike.py` lit un fichier MP3 passé en argument, sans interface graphique (juste `QMediaPlayer` + `QAudioOutput`, boucle d'événements minimale)
- Le script teste également un fichier MKV/H.265 si disponible, et note le résultat (succès ou `QMediaPlayer.Error`)
- Un fichier `spike/BACKEND_NOTES.md` résume : version de Qt installée, backend actif observé, formats testés avec succès/échec

**Fichiers concernés :** `spike/audio_spike.py`, `spike/BACKEND_NOTES.md`

**Dépendances :** US-001

**Notes pour Claude Code :** `BACKEND_NOTES.md` est un artefact de documentation, pas de code — il doit être rempli avec des résultats réels d'exécution, pas des suppositions. Si l'exécution n'est pas possible dans l'environnement de Claude Code (pas d'accès à un vrai fichier vidéo/affichage), documenter explicitement cette limite plutôt que d'inventer un résultat.

---

## Phase 1 — Squelette d'architecture

### US-010 — Créer la structure de dossiers du projet

**En tant que** développeur, **je veux** la structure de dossiers définie dans le PRD (section 4.2) en place avec des fichiers vides ou des stubs, **afin de** poser les fondations avant d'écrire la moindre logique métier.

**Critères d'acceptation :**
- L'arborescence suivante existe, avec des fichiers vides ou contenant uniquement des imports/classes stub :
```
media_player/
├── main.py
├── core/
│   ├── __init__.py
│   ├── player_engine.py
│   ├── playlist_manager.py
│   └── models.py
├── ui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── controls_widget.py
│   ├── progress_widget.py
│   ├── playlist_widget.py
│   └── video_widget.py
├── viewmodels/
│   ├── __init__.py
│   └── player_viewmodel.py
├── utils/
│   ├── __init__.py
│   └── formatters.py
└── tests/
    ├── __init__.py
    ├── test_player_engine.py
    ├── test_playlist_manager.py
    └── test_ui_integration.py
```
- `main.py` lance une fenêtre Qt vide (`QMainWindow` sans widgets) sans erreur

**Fichiers concernés :** tous les fichiers listés ci-dessus

**Dépendances :** US-000

**Notes pour Claude Code :** respecter strictement cette arborescence, ne pas la réorganiser même si une autre convention semble plus idiomatique — elle est actée dans le PRD et sert de référence pour toutes les stories suivantes.

---

### US-011 — Définir les modèles de données

**En tant que** développeur, **je veux** des dataclasses typées représentant les concepts métier (média, état de lecture), **afin de** disposer d'un vocabulaire commun avant d'écrire la logique.

**Critères d'acceptation :**
- `core/models.py` contient une dataclass `MediaItem` avec au minimum : `file_path: Path`, `display_name: str`, `duration_ms: int | None`
- `core/models.py` contient une énumération ou dataclass `PlaybackState` couvrant au minimum : `STOPPED`, `PLAYING`, `PAUSED`, `ERROR`
- Ces classes n'importent rien de `PyQt6.QtWidgets` (uniquement `dataclasses`, `pathlib`, `enum` de la stdlib)
- Un test `tests/test_models.py` instancie chaque classe et vérifie ses champs par défaut

**Fichiers concernés :** `core/models.py`, `tests/test_models.py`

**Dépendances :** US-010, US-013 (pour que pytest soit disponible — voir note ci-dessous)

**Notes pour Claude Code :** cette story peut être codée avant US-013, mais son test ne pourra être exécuté qu'une fois pytest installé (US-013). Écrire le test dès maintenant, l'exécuter après US-013.

---

### US-012 — Mettre en place les outils de qualité (lint + formatage)

**En tant que** développeur, **je veux** un linter et un formateur configurés, **afin de** garder une base de code cohérente dès le premier commit, en particulier pour un dépôt public.

**Critères d'acceptation :**
- `ruff` est ajouté à `requirements.txt` (ou `requirements-dev.txt` séparé)
- Un fichier `pyproject.toml` ou `ruff.toml` configure au minimum : longueur de ligne, règles de base (pyflakes + pycodestyle)
- La commande `ruff check .` s'exécute sans erreur sur le code existant

**Fichiers concernés :** `pyproject.toml` (ou `ruff.toml`), `requirements-dev.txt`

**Dépendances :** US-010

**Notes pour Claude Code :** séparer les dépendances de développement (`requirements-dev.txt`) des dépendances d'exécution (`requirements.txt`) pour que l'utilisateur final n'ait pas besoin d'installer `ruff`/`pytest`.

---

### US-013 — Mettre en place pytest et pytest-qt

**En tant que** développeur, **je veux** un framework de test fonctionnel incluant le support des widgets Qt, **afin de** pouvoir écrire des tests dès la Phase 2.

**Critères d'acceptation :**
- `pytest` et `pytest-qt` sont ajoutés à `requirements-dev.txt`
- Un test trivial (`tests/test_smoke.py`) vérifie que l'import de `PyQt6.QtWidgets` fonctionne et que `QApplication` peut être instanciée
- La commande `pytest` à la racine du projet s'exécute sans erreur et rapporte au moins un test passant

**Fichiers concernés :** `requirements-dev.txt`, `tests/test_smoke.py`, `tests/conftest.py` (fixture `qapp` si nécessaire)

**Dépendances :** US-010

**Notes pour Claude Code :** `pytest-qt` fournit la fixture `qtbot` nécessaire pour simuler des clics/interactions dans les tests UI de phases ultérieures — s'assurer qu'elle est bien détectée (`pytest --fixtures | grep qtbot`).

---

### US-014 — Mettre en place la CI GitHub Actions basique

**En tant que** développeur, **je veux** une CI qui exécute lint + tests à chaque push, **afin de** détecter les régressions immédiatement, en particulier pour un dépôt public consultable par d'autres développeurs.

**Critères d'acceptation :**
- Un fichier `.github/workflows/ci.yml` exécute, sur chaque push/PR : installation des dépendances, `ruff check .`, `pytest`
- Le workflow cible `ubuntu-latest` a minima (macOS runner optionnel, plus coûteux en minutes CI)
- Le badge de statut CI est ajouté au `README.md`

**Fichiers concernés :** `.github/workflows/ci.yml`, `README.md`

**Dépendances :** US-012, US-013

**Notes pour Claude Code :** sur `ubuntu-latest`, `pytest-qt` nécessite un serveur X virtuel (`xvfb`) pour les tests instanciant de vrais widgets — prévoir `xvfb-run` ou l'action `pyvista/setup-headless-display-action` dans le workflow.

---

## Phase 2 — Lecture basique

### US-020 — Implémenter le moteur de lecture (core)

**En tant que** développeur, **je veux** une classe `PlayerEngine` encapsulant `QMediaPlayer` sans dépendre des widgets, **afin de** respecter la séparation MVVM définie dans le PRD et permettre des tests unitaires sans instancier de fenêtre.

**Critères d'acceptation :**
- `core/player_engine.py` définit une classe `PlayerEngine` avec au minimum les méthodes : `load(media_item: MediaItem)`, `play()`, `pause()`, `stop()`
- `PlayerEngine` expose l'état courant via une propriété `state: PlaybackState`
- `PlayerEngine` n'importe rien de `PyQt6.QtWidgets` (uniquement `PyQt6.QtMultimedia` et `PyQt6.QtCore` pour les signaux)
- Un test `tests/test_player_engine.py` vérifie que `load()` suivi de `play()` change l'état à `PLAYING` (avec un fichier de test fourni dans `tests/fixtures/`)

**Fichiers concernés :** `core/player_engine.py`, `tests/test_player_engine.py`, `tests/fixtures/sample.mp3` (petit fichier audio de test, quelques secondes)

**Dépendances :** US-011, US-013

**Notes pour Claude Code :** générer ou fournir un fichier audio de test minimal (silence de 2 secondes suffit) pour ne pas dépendre d'assets externes volumineux dans le dépôt public. Si un fichier audio ne peut pas être généré directement, documenter clairement dans `tests/fixtures/README.md` comment l'obtenir/générer.

---

### US-021 — Créer la fenêtre principale et le point d'entrée

**En tant que** développeur, **je veux** une `QMainWindow` fonctionnelle qui s'ouvre au lancement de l'application, **afin de** disposer d'un point d'ancrage pour tous les widgets à venir.

**Critères d'acceptation :**
- `ui/main_window.py` définit une classe `MainWindow(QMainWindow)` avec un titre de fenêtre ("Lecteur Média" ou équivalent) et une taille par défaut raisonnable (ex. 900x600)
- `main.py` instancie `QApplication`, crée une `MainWindow`, l'affiche, et lance la boucle d'événements
- L'application se lance sans erreur via `python main.py` et affiche une fenêtre vide

**Fichiers concernés :** `main.py`, `ui/main_window.py`

**Dépendances :** US-010

**Notes pour Claude Code :** ne pas encore intégrer `PlayerEngine` ici — cette story est purement structurelle (fenêtre vide). L'intégration se fait en US-022.

---

### US-022 — Intégrer l'ouverture de fichier et l'affichage vidéo

**En tant qu'**utilisateur, **je veux** ouvrir un fichier vidéo via un dialogue de sélection et le voir s'afficher, **afin de** commencer à utiliser le lecteur.

**Critères d'acceptation (F1, F6 du PRD) :**
- Un menu ou bouton "Ouvrir un fichier" déclenche `QFileDialog.getOpenFileName` filtré sur les extensions vidéo/audio courantes
- Le fichier sélectionné est chargé dans `PlayerEngine` via le `PlayerViewModel` (voir US-023)
- La vidéo s'affiche dans un `QVideoWidget` intégré à `MainWindow`, en conservant le ratio d'aspect lors du redimensionnement de la fenêtre
- Étant donné un fichier audio (pas de piste vidéo), le `QVideoWidget` reste vide/neutre sans erreur

**Fichiers concernés :** `ui/main_window.py`, `ui/video_widget.py`

**Dépendances :** US-020, US-021, US-023

**Notes pour Claude Code :** `QVideoWidget` doit être connecté à `QMediaPlayer.setVideoOutput()` — cette connexion doit être faite via le ViewModel, pas directement dans le widget, pour rester cohérent avec le flux de données décrit en section 4.3 du PRD.

---

### US-023 — Créer le ViewModel de lecture et les contrôles play/pause/stop

**En tant qu'**utilisateur, **je veux** des boutons play/pause/stop fonctionnels, **afin de** contrôler la lecture (F2, F3 du PRD).

**Critères d'acceptation :**
- `viewmodels/player_viewmodel.py` définit `PlayerViewModel(QObject)` avec des signaux Qt (`pyqtSignal`) exposant les changements d'état pertinents pour l'UI (ex. `state_changed`, `position_changed`)
- `PlayerViewModel` fait le pont entre `PlayerEngine` (logique pure) et les widgets (aucune logique métier dans les widgets eux-mêmes)
- `ui/controls_widget.py` définit un widget avec trois boutons (play, pause, stop) qui émettent des signaux consommés par le ViewModel
- Cliquer sur play lance la lecture, pause la met en pause, stop revient à la position 0 et arrête la lecture
- Un test `tests/test_ui_integration.py` utilise `qtbot` pour simuler un clic sur play et vérifier (via un mock ou un fichier réel court) que l'état passe à `PLAYING`

**Fichiers concernés :** `viewmodels/player_viewmodel.py`, `ui/controls_widget.py`, `tests/test_ui_integration.py`

**Dépendances :** US-020, US-021

**Notes pour Claude Code :** c'est la story charnière qui valide le pattern MVVM du PRD (section 4.3) — vérifier explicitement, avant de continuer, qu'aucun import `PyQt6.QtWidgets` n'existe dans `core/player_engine.py`. C'est un critère d'acceptation implicite mais non négociable de l'ensemble du projet.

---

## Phase 3 — Contrôles avancés

### US-030 — Implémenter la barre de progression avec seek

**En tant qu'**utilisateur, **je veux** une barre de progression cliquable et draggable affichant la position de lecture, **afin de** naviguer dans le média (F4 du PRD).

**Critères d'acceptation :**
- `ui/progress_widget.py` définit un `QSlider` horizontal synchronisé avec la position de lecture via le ViewModel
- Le slider se met à jour automatiquement pendant la lecture (polling ou signal `positionChanged` de `QMediaPlayer`, exposé via le ViewModel)
- Cliquer/glisser sur le slider déclenche un seek (`PlayerEngine.set_position(ms)`) vers la position correspondante
- Pendant que l'utilisateur drague le slider, la position affichée ne doit pas être écrasée par les mises à jour automatiques de lecture (éviter le conflit UI classique)
- Deux `QLabel` affichent le temps écoulé et la durée totale au format `mm:ss`, via `utils/formatters.py`

**Fichiers concernés :** `ui/progress_widget.py`, `utils/formatters.py`, `tests/test_formatters.py`

**Dépendances :** US-023

**Notes pour Claude Code :** le conflit "drag utilisateur vs mise à jour automatique" est un piège classique — utiliser un flag interne (`is_seeking: bool`) sur le widget, mis à `True` sur `sliderPressed` et `False` sur `sliderReleased`, pour ignorer les mises à jour de position pendant que l'utilisateur drague.

---

### US-031 — Implémenter le contrôle du volume

**En tant qu'**utilisateur, **je veux** régler le volume et pouvoir couper le son, **afin de** contrôler l'expérience d'écoute (F5 du PRD).

**Critères d'acceptation :**
- Un `QSlider` vertical ou horizontal (0-100) contrôle `QAudioOutput.setVolume()` via le ViewModel
- Un bouton mute/unmute bascule le volume à 0 et restaure la valeur précédente à la réactivation
- L'état du slider et du bouton mute restent synchronisés (si l'utilisateur remonte le slider depuis 0, le mute se désactive automatiquement)

**Fichiers concernés :** `ui/controls_widget.py` (ou nouveau `ui/volume_widget.py` si la séparation est plus propre)

**Dépendances :** US-023

**Notes pour Claude Code :** si un nouveau fichier `ui/volume_widget.py` est créé, penser à l'ajouter au PRD (section 4.2) pour garder la documentation d'architecture synchronisée avec le code réel.

---

### US-032 — Implémenter les raccourcis clavier

**En tant qu'**utilisateur, **je veux** contrôler le lecteur au clavier, **afin de** ne pas dépendre uniquement de la souris (F11 du PRD).

**Critères d'acceptation :**
- Espace : play/pause
- Flèche droite : avance de 5 secondes
- Flèche gauche : recule de 5 secondes
- Flèche haut : volume +5%
- Flèche bas : volume -5%
- Les raccourcis fonctionnent uniquement quand la fenêtre principale a le focus (pas de conflit si le focus est sur un champ de texte, s'il y en a un)

**Fichiers concernés :** `ui/main_window.py` (gestion des `QShortcut` ou surcharge de `keyPressEvent`)

**Dépendances :** US-023, US-030, US-031

**Notes pour Claude Code :** préférer `QShortcut` avec `QKeySequence` plutôt qu'une surcharge manuelle de `keyPressEvent`, pour bénéficier de la gestion native des conflits de focus Qt.

---

## Phase 4 — Playlist

### US-040 — Implémenter le gestionnaire de playlist (core)

**En tant que** développeur, **je veux** une classe `PlaylistManager` gérant la liste de médias indépendamment de l'UI, **afin de** respecter la séparation MVVM.

**Critères d'acceptation :**
- `core/playlist_manager.py` définit une classe `PlaylistManager` avec : `add(media_item)`, `remove(index)`, `next()`, `previous()`, `current: MediaItem | None`
- `next()`/`previous()` gèrent correctement les bords (pas d'exception en début/fin de liste ; comportement à définir explicitement : bloquer au dernier élément pour le MVP, le mode boucle étant F13/V2)
- Un test `tests/test_playlist_manager.py` couvre : ajout, suppression, navigation, comportement aux bords

**Fichiers concernés :** `core/playlist_manager.py`, `tests/test_playlist_manager.py`

**Dépendances :** US-011

**Notes pour Claude Code :** ne pas implémenter le mode répétition/aléatoire ici (F13/F14 sont V2, hors scope MVP selon le PRD) — se limiter strictement à la navigation linéaire.

---

### US-041 — Afficher la playlist dans l'UI

**En tant qu'**utilisateur, **je veux** voir la liste des fichiers ajoutés et pouvoir en sélectionner un pour le lire, **afin de** gérer plusieurs médias (F7 du PRD).

**Critères d'acceptation :**
- `ui/playlist_widget.py` définit un `QListWidget` (ou `QListView` + modèle) affichant `display_name` de chaque `MediaItem`
- Double-cliquer sur un élément le charge et lance sa lecture via le ViewModel
- Un bouton ou raccourci (touche Suppr) retire l'élément sélectionné de la playlist
- L'élément en cours de lecture est visuellement distingué (surlignage, icône, ou gras)

**Fichiers concernés :** `ui/playlist_widget.py`

**Dépendances :** US-040, US-023

**Notes pour Claude Code :** connecter `PlaylistManager` au `PlayerViewModel` (pas directement au widget) pour garder le flux de données cohérent avec la section 4.3 du PRD.

---

### US-042 — Implémenter la navigation next/previous

**En tant qu'**utilisateur, **je veux** passer au fichier suivant/précédent de la playlist, **afin de** ne pas revenir systématiquement à la playlist pour changer de piste (F8 du PRD).

**Critères d'acceptation :**
- Deux boutons (ou raccourcis) déclenchent `PlaylistManager.next()` / `.previous()` via le ViewModel
- Le nouveau média est automatiquement chargé et la lecture démarre si le lecteur était déjà en lecture (comportement à documenter clairement si différent)
- Arrivé en fin de playlist, le bouton "suivant" se désactive (ou ne fait rien, comportement cohérent avec US-040)

**Fichiers concernés :** `ui/controls_widget.py`, `viewmodels/player_viewmodel.py`

**Dépendances :** US-040, US-041

**Notes pour Claude Code :** décider explicitement (et documenter en commentaire) si "suivant" pendant une lecture en pause reprend automatiquement la lecture ou reste en pause — ce comportement n'est pas spécifié dans le PRD et doit être tranché ici pour éviter l'ambiguïté silencieuse.

---

### US-043 — Implémenter le drag & drop de fichiers

**En tant qu'**utilisateur, **je veux** glisser des fichiers depuis le Finder vers la fenêtre pour les ajouter à la playlist, **afin de** ne pas systématiquement passer par le dialogue d'ouverture (F9 du PRD).

**Critères d'acceptation :**
- `MainWindow` accepte le drag & drop (`setAcceptDrops(True)`, `dragEnterEvent`, `dropEvent`)
- Glisser un ou plusieurs fichiers ajoute chacun à la playlist via `PlaylistManager`
- Les fichiers dont l'extension n'est pas reconnue sont ignorés silencieusement ou signalés (cohérent avec la gestion d'erreurs de la Phase 5, US-050)

**Fichiers concernés :** `ui/main_window.py`

**Dépendances :** US-040

**Notes pour Claude Code :** filtrer les extensions dès le `dropEvent` (avant ajout à la playlist), pour ne pas polluer `PlaylistManager` avec des fichiers invalides qui échoueraient uniquement au moment de la lecture.

---

## Phase 5 — Robustesse

### US-050 — Implémenter la gestion des erreurs de lecture

**En tant qu'**utilisateur, **je veux** un message clair si un fichier est corrompu ou dans un format non supporté, **afin de** comprendre ce qui se passe sans que l'application ne plante (F10 du PRD).

**Critères d'acceptation :**
- `PlayerEngine` écoute le signal `errorOccurred` de `QMediaPlayer` et le remonte via le ViewModel
- Une boîte de dialogue (`QMessageBox`) ou une bannière dans l'UI affiche un message compréhensible (pas le message technique brut de Qt) selon le type d'erreur (`QMediaPlayer.Error`)
- Après une erreur, l'état revient à `STOPPED` (ou `ERROR` puis `STOPPED`) sans que l'application ne devienne inutilisable
- Un test simule le chargement d'un fichier inexistant et vérifie que l'erreur est capturée sans exception non gérée

**Fichiers concernés :** `core/player_engine.py`, `viewmodels/player_viewmodel.py`, `ui/main_window.py`, `tests/test_player_engine.py`

**Dépendances :** US-020

**Notes pour Claude Code :** faire une table de correspondance explicite entre les valeurs de `QMediaPlayer.Error` (`ResourceError`, `FormatError`, `NetworkError`, `AccessDeniedError`) et des messages utilisateur en français, plutôt que d'afficher l'énumération brute.

---

### US-051 — Atteindre la couverture de tests cible sur `core/`

**En tant que** développeur, **je veux** au moins 70% de couverture de tests sur `core/`, **afin de** respecter l'exigence non fonctionnelle du PRD (section 5) avant de packager l'application.

**Critères d'acceptation :**
- `pytest-cov` est ajouté à `requirements-dev.txt`
- La commande `pytest --cov=core --cov-report=term-missing` rapporte une couverture >= 70% sur `core/player_engine.py`, `core/playlist_manager.py`, `core/models.py`
- Les lignes non couvertes restantes sont documentées si elles sont volontairement exclues (ex. code défensif difficile à déclencher)

**Fichiers concernés :** `requirements-dev.txt`, tests existants complétés si nécessaire

**Dépendances :** toutes les stories `core/` précédentes (US-020, US-040, US-050)

**Notes pour Claude Code :** ne pas artificiellement gonfler la couverture avec des tests triviaux sans assertions utiles — privilégier des tests couvrant les branches d'erreur réelles (fichier introuvable, playlist vide, etc.) plutôt que de viser un pourcentage vide de sens.

---

## Phase 6 — Packaging

### US-060 — Packager l'application avec PyInstaller

**En tant qu'**utilisateur final, **je veux** un exécutable autonome, **afin de** lancer l'application sans installer Python ni les dépendances manuellement.

**Critères d'acceptation :**
- `PyInstaller` est ajouté à `requirements-dev.txt`
- Un fichier de spec (`media_player.spec`) ou une commande documentée dans le README génère un exécutable macOS (`.app`)
- L'exécutable inclut correctement les bibliothèques FFmpeg nécessaires à QtMultimedia (cf. note technique du PRD section 10 sur le déploiement dynamique des bibliothèques FFmpeg sur macOS)
- L'exécutable généré se lance et permet de lire un fichier MP4 de test sans avoir Python installé sur la machine de test (si possible à vérifier ; sinon documenter la limite de vérification)

**Fichiers concernés :** `media_player.spec`, `README.md` (section packaging)

**Dépendances :** US-050, US-051

**Notes pour Claude Code :** le point de vigilance principal ici est le lien dynamique de FFmpeg sur macOS — vérifier explicitement, après packaging, que les bibliothèques FFmpeg sont bien embarquées dans le bundle `.app` (via `otool -L` sur le binaire final, par exemple) et pas seulement présentes sur la machine de build.

---

### US-061 — Rédiger la documentation utilisateur finale

**En tant qu'**utilisateur (ou visiteur du dépôt public), **je veux** un README complet, **afin de** comprendre comment installer, lancer et contribuer au projet.

**Critères d'acceptation :**
- Le `README.md` contient : description du projet, captures d'écran ou GIF de démonstration, instructions d'installation (dev et utilisateur final via l'exécutable packagé), liste des fonctionnalités MVP, licence (GPLv3, cohérente avec PyQt6), lien vers ce fichier de user stories et le PRD si pertinent pour un lecteur curieux
- Une licence (`LICENSE`, GPLv3) est présente à la racine du dépôt

**Fichiers concernés :** `README.md`, `LICENSE`

**Dépendances :** US-060

**Notes pour Claude Code :** cette story est la dernière du MVP — une fois complétée, comparer explicitement l'état du projet aux 7 critères d'acceptation du MVP listés en section 8 du PRD, un par un, avant de considérer le projet "terminé".

---
---

# User Stories (English) — Audio/Video Player, PyQt6 + QtMultimedia

**Companion document to the PRD** (`PRD_Lecteur_Media_PyQt6.md`)
**Usage:** this file is designed to be executed sequentially by Claude Code, story by story, in the order given. Each story is self-contained, testable, and references the architecture defined in the PRD (section 4.2).

**ID convention:** `US-PPNN` where `PP` = phase number (00 to 06), `NN` = story number within the phase.

**Rule for Claude Code:** do not move to the next story until all acceptance criteria of the current story are verified (including passing tests). An atomic commit per story is recommended (commit message = story ID + title).

---

## Phase 0 — Technical spike

### US-000 — Set up the development environment

**As a** developer, **I want** an isolated, reproducible Python environment, **so that** the project behaves identically on every re-run.

**Acceptance criteria:**
- A `venv` is created at the project root (`python3 -m venv venv`)
- A `requirements.txt` file exists with at least `PyQt6` (latest stable 6.x version)
- A `.gitignore` file excludes `venv/`, `__pycache__/`, `*.pyc`
- A minimal `README.md` states: the Python version used, the venv activation command, and the dependency installation command

**Files involved:** `requirements.txt`, `.gitignore`, `README.md`

**Dependencies:** none

**Notes for Claude Code:** do not yet add `pytest`/`pytest-qt` here — this is handled in US-013. Keep this to the strict minimum needed to run PyQt6.

---

### US-001 — Validate basic video playback

**As a** developer, **I want** a minimal script proving that `QMediaPlayer` + `QVideoWidget` can play a local MP4 file, **so that** the technical stack is validated before investing in the full architecture.

**Acceptance criteria:**
- A `spike/video_spike.py` script opens a Qt window with a `QVideoWidget`
- The script plays an MP4 file passed as a command-line argument (`python spike/video_spike.py path/to/file.mp4`)
- Playback starts automatically on opening and the image renders correctly
- The script logs the active Qt Multimedia backend to the console at startup (the `QT_MEDIA_BACKEND` environment variable if set, otherwise an explicit "default backend" note)

**Files involved:** `spike/video_spike.py`

**Dependencies:** US-000

**Notes for Claude Code:** this code is disposable; no unit tests are required here, and MVVM architecture compliance is not required — this is an exploratory script isolated in `spike/`, which must not be imported by the rest of the project.

---

### US-002 — Validate basic audio playback and the backend detector

**As a** developer, **I want** to validate MP3 playback and document which backend is actually in use on my macOS machine, **so that** the risk identified in PRD sections 6/9 is resolved before Phase 2.

**Acceptance criteria:**
- A `spike/audio_spike.py` script plays an MP3 file passed as an argument, with no graphical interface (just `QMediaPlayer` + `QAudioOutput`, a minimal event loop)
- The script also tests an MKV/H.265 file if one is available, noting the result (success or `QMediaPlayer.Error`)
- A `spike/BACKEND_NOTES.md` file summarises: the installed Qt version, the observed active backend, and formats tested with success/failure

**Files involved:** `spike/audio_spike.py`, `spike/BACKEND_NOTES.md`

**Dependencies:** US-001

**Notes for Claude Code:** `BACKEND_NOTES.md` is a documentation artefact, not code — it must be filled in with actual execution results, not assumptions. If execution is not possible in Claude Code's environment (no access to a real video file/display), explicitly document that limitation rather than fabricating a result.

---

## Phase 1 — Architecture skeleton

### US-010 — Create the project folder structure

**As a** developer, **I want** the folder structure defined in the PRD (section 4.2) in place, with empty files or stubs, **so that** the foundations are laid before any business logic is written.

**Acceptance criteria:**
- The following tree exists, with empty files or files containing only stub imports/classes:
```
media_player/
├── main.py
├── core/
│   ├── __init__.py
│   ├── player_engine.py
│   ├── playlist_manager.py
│   └── models.py
├── ui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── controls_widget.py
│   ├── progress_widget.py
│   ├── playlist_widget.py
│   └── video_widget.py
├── viewmodels/
│   ├── __init__.py
│   └── player_viewmodel.py
├── utils/
│   ├── __init__.py
│   └── formatters.py
└── tests/
    ├── __init__.py
    ├── test_player_engine.py
    ├── test_playlist_manager.py
    └── test_ui_integration.py
```
- `main.py` launches an empty Qt window (`QMainWindow` with no widgets) without error

**Files involved:** all files listed above

**Dependencies:** US-000

**Notes for Claude Code:** follow this tree strictly, do not reorganise it even if another convention seems more idiomatic — it is fixed in the PRD and serves as the reference for every subsequent story.

---

### US-011 — Define the data models

**As a** developer, **I want** typed dataclasses representing the core business concepts (media, playback state), **so that** a shared vocabulary exists before any logic is written.

**Acceptance criteria:**
- `core/models.py` contains a `MediaItem` dataclass with at least: `file_path: Path`, `display_name: str`, `duration_ms: int | None`
- `core/models.py` contains an enum or dataclass `PlaybackState` covering at least: `STOPPED`, `PLAYING`, `PAUSED`, `ERROR`
- These classes import nothing from `PyQt6.QtWidgets` (only `dataclasses`, `pathlib`, `enum` from the standard library)
- A `tests/test_models.py` test instantiates each class and checks its default fields

**Files involved:** `core/models.py`, `tests/test_models.py`

**Dependencies:** US-010, US-013 (for pytest availability — see note below)

**Notes for Claude Code:** this story can be coded before US-013, but its test can only be run once pytest is installed (US-013). Write the test now, run it after US-013.

---

### US-012 — Set up quality tooling (lint + formatting)

**As a** developer, **I want** a configured linter and formatter, **so that** the codebase stays consistent from the first commit, especially given a public repository.

**Acceptance criteria:**
- `ruff` is added to `requirements.txt` (or a separate `requirements-dev.txt`)
- A `pyproject.toml` or `ruff.toml` file configures at least: line length, basic rule sets (pyflakes + pycodestyle)
- The `ruff check .` command runs without error on the existing code

**Files involved:** `pyproject.toml` (or `ruff.toml`), `requirements-dev.txt`

**Dependencies:** US-010

**Notes for Claude Code:** keep development dependencies (`requirements-dev.txt`) separate from runtime dependencies (`requirements.txt`) so end users do not need to install `ruff`/`pytest`.

---

### US-013 — Set up pytest and pytest-qt

**As a** developer, **I want** a working test framework including Qt widget support, **so that** tests can be written starting in Phase 2.

**Acceptance criteria:**
- `pytest` and `pytest-qt` are added to `requirements-dev.txt`
- A trivial test (`tests/test_smoke.py`) checks that `PyQt6.QtWidgets` imports correctly and that `QApplication` can be instantiated
- Running `pytest` from the project root succeeds without error and reports at least one passing test

**Files involved:** `requirements-dev.txt`, `tests/test_smoke.py`, `tests/conftest.py` (a `qapp` fixture if needed)

**Dependencies:** US-010

**Notes for Claude Code:** `pytest-qt` provides the `qtbot` fixture needed to simulate clicks/interactions in the UI tests of later phases — make sure it is correctly detected (`pytest --fixtures | grep qtbot`).

---

### US-014 — Set up basic GitHub Actions CI

**As a** developer, **I want** CI that runs lint + tests on every push, **so that** regressions are caught immediately, particularly given a public repository that other developers may browse.

**Acceptance criteria:**
- A `.github/workflows/ci.yml` file runs, on every push/PR: dependency installation, `ruff check .`, `pytest`
- The workflow targets `ubuntu-latest` at minimum (a macOS runner is optional, as it consumes more CI minutes)
- A CI status badge is added to `README.md`

**Files involved:** `.github/workflows/ci.yml`, `README.md`

**Dependencies:** US-012, US-013

**Notes for Claude Code:** on `ubuntu-latest`, `pytest-qt` requires a virtual X server (`xvfb`) for tests that instantiate real widgets — plan for `xvfb-run` or the `pyvista/setup-headless-display-action` action in the workflow.

---

## Phase 2 — Basic playback

### US-020 — Implement the playback engine (core)

**As a** developer, **I want** a `PlayerEngine` class wrapping `QMediaPlayer` with no dependency on widgets, **so that** the MVVM separation defined in the PRD is respected, and unit tests can run without instantiating a window.

**Acceptance criteria:**
- `core/player_engine.py` defines a `PlayerEngine` class with at least the methods: `load(media_item: MediaItem)`, `play()`, `pause()`, `stop()`
- `PlayerEngine` exposes the current state via a `state: PlaybackState` property
- `PlayerEngine` imports nothing from `PyQt6.QtWidgets` (only `PyQt6.QtMultimedia` and `PyQt6.QtCore` for signals)
- A `tests/test_player_engine.py` test checks that `load()` followed by `play()` changes the state to `PLAYING` (using a test file provided in `tests/fixtures/`)

**Files involved:** `core/player_engine.py`, `tests/test_player_engine.py`, `tests/fixtures/sample.mp3` (a small test audio file, a few seconds long)

**Dependencies:** US-011, US-013

**Notes for Claude Code:** generate or provide a minimal test audio file (a 2-second silence is enough) to avoid depending on large external assets in the public repository. If an audio file cannot be generated directly, clearly document in `tests/fixtures/README.md` how to obtain/generate one.

---

### US-021 — Create the main window and entry point

**As a** developer, **I want** a working `QMainWindow` that opens when the application launches, **so that** there is an anchor point for all upcoming widgets.

**Acceptance criteria:**
- `ui/main_window.py` defines a `MainWindow(QMainWindow)` class with a window title ("Media Player" or equivalent) and a reasonable default size (e.g. 900x600)
- `main.py` instantiates `QApplication`, creates a `MainWindow`, shows it, and runs the event loop
- The application launches without error via `python main.py` and displays an empty window

**Files involved:** `main.py`, `ui/main_window.py`

**Dependencies:** US-010

**Notes for Claude Code:** do not integrate `PlayerEngine` here yet — this story is purely structural (empty window). Integration happens in US-022.

---

### US-022 — Integrate file opening and video display

**As a** user, **I want** to open a video file via a selection dialog and see it displayed, **so that** I can start using the player.

**Acceptance criteria (PRD F1, F6):**
- A menu or button "Open file" triggers `QFileDialog.getOpenFileName` filtered to common video/audio extensions
- The selected file is loaded into `PlayerEngine` via the `PlayerViewModel` (see US-023)
- The video renders inside a `QVideoWidget` embedded in `MainWindow`, preserving aspect ratio as the window is resized
- Given an audio file (no video track), the `QVideoWidget` remains empty/neutral without error

**Files involved:** `ui/main_window.py`, `ui/video_widget.py`

**Dependencies:** US-020, US-021, US-023

**Notes for Claude Code:** `QVideoWidget` must be connected via `QMediaPlayer.setVideoOutput()` — this connection should be made through the ViewModel, not directly in the widget, to remain consistent with the data flow described in PRD section 4.3.

---

### US-023 — Create the playback ViewModel and play/pause/stop controls

**As a** user, **I want** working play/pause/stop buttons, **so that** I can control playback (PRD F2, F3).

**Acceptance criteria:**
- `viewmodels/player_viewmodel.py` defines `PlayerViewModel(QObject)` with Qt signals (`pyqtSignal`) exposing state changes relevant to the UI (e.g. `state_changed`, `position_changed`)
- `PlayerViewModel` bridges `PlayerEngine` (pure logic) and the widgets (no business logic inside the widgets themselves)
- `ui/controls_widget.py` defines a widget with three buttons (play, pause, stop) that emit signals consumed by the ViewModel
- Clicking play starts playback, pause pauses it, stop returns to position 0 and stops playback
- A `tests/test_ui_integration.py` test uses `qtbot` to simulate a click on play and verify (via a mock or a short real file) that the state changes to `PLAYING`

**Files involved:** `viewmodels/player_viewmodel.py`, `ui/controls_widget.py`, `tests/test_ui_integration.py`

**Dependencies:** US-020, US-021

**Notes for Claude Code:** this is the pivotal story that validates the PRD's MVVM pattern (section 4.3) — explicitly check, before continuing, that no `PyQt6.QtWidgets` import exists in `core/player_engine.py`. This is an implicit but non-negotiable acceptance criterion for the whole project.

---

## Phase 3 — Advanced controls

### US-030 — Implement the progress bar with seeking

**As a** user, **I want** a clickable and draggable progress bar showing playback position, **so that** I can navigate within the media (PRD F4).

**Acceptance criteria:**
- `ui/progress_widget.py` defines a horizontal `QSlider` synchronised with playback position via the ViewModel
- The slider updates automatically during playback (polling, or `QMediaPlayer`'s `positionChanged` signal, exposed via the ViewModel)
- Clicking/dragging the slider triggers a seek (`PlayerEngine.set_position(ms)`) to the corresponding position
- While the user is dragging the slider, the displayed position must not be overwritten by automatic playback updates (avoiding the classic UI race condition)
- Two `QLabel` widgets display elapsed time and total duration in `mm:ss` format, via `utils/formatters.py`

**Files involved:** `ui/progress_widget.py`, `utils/formatters.py`, `tests/test_formatters.py`

**Dependencies:** US-023

**Notes for Claude Code:** the "user drag vs automatic update" conflict is a classic pitfall — use an internal flag (`is_seeking: bool`) on the widget, set to `True` on `sliderPressed` and `False` on `sliderReleased`, to ignore position updates while the user is dragging.

---

### US-031 — Implement volume control

**As a** user, **I want** to adjust the volume and mute the sound, **so that** I can control the listening experience (PRD F5).

**Acceptance criteria:**
- A `QSlider` (vertical or horizontal, 0–100) controls `QAudioOutput.setVolume()` via the ViewModel
- A mute/unmute button sets the volume to 0 and restores the previous value when re-enabled
- The slider and mute button states stay synchronised (if the user raises the slider from 0, mute automatically deactivates)

**Files involved:** `ui/controls_widget.py` (or a new `ui/volume_widget.py` if a cleaner separation is preferred)

**Dependencies:** US-023

**Notes for Claude Code:** if a new `ui/volume_widget.py` file is created, remember to add it to the PRD (section 4.2) so the architecture documentation stays in sync with the actual code.

---

### US-032 — Implement keyboard shortcuts

**As a** user, **I want** to control the player from the keyboard, **so that** I am not solely dependent on the mouse (PRD F11).

**Acceptance criteria:**
- Space: play/pause
- Right arrow: skip forward 5 seconds
- Left arrow: skip back 5 seconds
- Up arrow: volume +5%
- Down arrow: volume -5%
- Shortcuts only work when the main window has focus (no conflict if focus is on a text field, should one exist)

**Files involved:** `ui/main_window.py` (`QShortcut` handling, or an overridden `keyPressEvent`)

**Dependencies:** US-023, US-030, US-031

**Notes for Claude Code:** prefer `QShortcut` with `QKeySequence` over a manual `keyPressEvent` override, to benefit from Qt's native focus-conflict handling.

---

## Phase 4 — Playlist

### US-040 — Implement the playlist manager (core)

**As a** developer, **I want** a `PlaylistManager` class managing the media list independently of the UI, **so that** the MVVM separation is respected.

**Acceptance criteria:**
- `core/playlist_manager.py` defines a `PlaylistManager` class with: `add(media_item)`, `remove(index)`, `next()`, `previous()`, `current: MediaItem | None`
- `next()`/`previous()` correctly handle edge cases (no exception at the start/end of the list; the exact behaviour must be explicitly defined: stopping at the last item for the MVP, since repeat mode is F13/V2)
- A `tests/test_playlist_manager.py` test covers: adding, removing, navigation, edge-case behaviour

**Files involved:** `core/playlist_manager.py`, `tests/test_playlist_manager.py`

**Dependencies:** US-011

**Notes for Claude Code:** do not implement repeat/shuffle mode here (F13/F14 are V2, out of MVP scope per the PRD) — strictly limit this to linear navigation.

---

### US-041 — Display the playlist in the UI

**As a** user, **I want** to see the list of added files and select one to play, **so that** I can manage multiple media items (PRD F7).

**Acceptance criteria:**
- `ui/playlist_widget.py` defines a `QListWidget` (or `QListView` + model) displaying each `MediaItem`'s `display_name`
- Double-clicking an item loads it and starts playback via the ViewModel
- A button or shortcut (Delete key) removes the selected item from the playlist
- The currently playing item is visually distinguished (highlight, icon, or bold text)

**Files involved:** `ui/playlist_widget.py`

**Dependencies:** US-040, US-023

**Notes for Claude Code:** connect `PlaylistManager` to `PlayerViewModel` (not directly to the widget) to keep the data flow consistent with PRD section 4.3.

---

### US-042 — Implement next/previous navigation

**As a** user, **I want** to move to the next/previous file in the playlist, **so that** I do not have to return to the playlist every time I want to change track (PRD F8).

**Acceptance criteria:**
- Two buttons (or shortcuts) trigger `PlaylistManager.next()` / `.previous()` via the ViewModel
- The new media item is automatically loaded, and playback starts if the player was already playing (behaviour to be documented clearly if different)
- At the end of the playlist, the "next" button is disabled (or does nothing, consistent with US-040's behaviour)

**Files involved:** `ui/controls_widget.py`, `viewmodels/player_viewmodel.py`

**Dependencies:** US-040, US-041

**Notes for Claude Code:** explicitly decide (and document in a comment) whether pressing "next" while paused automatically resumes playback or stays paused — this behaviour is not specified in the PRD and must be settled here to avoid silent ambiguity.

---

### US-043 — Implement file drag & drop

**As a** user, **I want** to drag files from Finder into the window to add them to the playlist, **so that** I do not always have to go through the open-file dialog (PRD F9).

**Acceptance criteria:**
- `MainWindow` accepts drag & drop (`setAcceptDrops(True)`, `dragEnterEvent`, `dropEvent`)
- Dragging one or more files adds each to the playlist via `PlaylistManager`
- Files with an unrecognised extension are silently ignored or flagged (consistent with the error handling of Phase 5, US-050)

**Files involved:** `ui/main_window.py`

**Dependencies:** US-040

**Notes for Claude Code:** filter extensions right in the `dropEvent` (before adding to the playlist), so as not to pollute `PlaylistManager` with invalid files that would only fail at playback time.

---

## Phase 5 — Robustness

### US-050 — Implement playback error handling

**As a** user, **I want** a clear message if a file is corrupted or in an unsupported format, **so that** I understand what happened without the application crashing (PRD F10).

**Acceptance criteria:**
- `PlayerEngine` listens for `QMediaPlayer`'s `errorOccurred` signal and surfaces it via the ViewModel
- A dialog (`QMessageBox`) or an in-UI banner displays an understandable message (not Qt's raw technical message) depending on the error type (`QMediaPlayer.Error`)
- After an error, the state returns to `STOPPED` (or `ERROR` then `STOPPED`) without the application becoming unusable
- A test simulates loading a non-existent file and verifies the error is caught without an unhandled exception

**Files involved:** `core/player_engine.py`, `viewmodels/player_viewmodel.py`, `ui/main_window.py`, `tests/test_player_engine.py`

**Dependencies:** US-020

**Notes for Claude Code:** build an explicit mapping between `QMediaPlayer.Error` values (`ResourceError`, `FormatError`, `NetworkError`, `AccessDeniedError`) and user-facing messages, rather than displaying the raw enum.

---

### US-051 — Reach the target test coverage on `core/`

**As a** developer, **I want** at least 70% test coverage on `core/`, **so that** the non-functional requirement from the PRD (section 5) is met before packaging the application.

**Acceptance criteria:**
- `pytest-cov` is added to `requirements-dev.txt`
- Running `pytest --cov=core --cov-report=term-missing` reports >= 70% coverage on `core/player_engine.py`, `core/playlist_manager.py`, `core/models.py`
- Any remaining uncovered lines are documented if intentionally excluded (e.g. defensive code that is hard to trigger)

**Files involved:** `requirements-dev.txt`, existing tests completed as needed

**Dependencies:** all previous `core/`-related stories (US-020, US-040, US-050)

**Notes for Claude Code:** do not artificially inflate coverage with trivial tests lacking meaningful assertions — prioritise tests covering real error branches (missing file, empty playlist, etc.) over chasing a percentage that is meaningless on its own.

---

## Phase 6 — Packaging

### US-060 — Package the application with PyInstaller

**As an** end user, **I want** a standalone executable, **so that** I can launch the application without manually installing Python or its dependencies.

**Acceptance criteria:**
- `PyInstaller` is added to `requirements-dev.txt`
- A spec file (`media_player.spec`) or a documented command in the README generates a macOS executable (`.app`)
- The executable correctly bundles the FFmpeg libraries needed by QtMultimedia (cf. the PRD section 10 technical note on dynamic linking of FFmpeg libraries on macOS)
- The generated executable launches and can play a test MP4 file without Python installed on the test machine (verify if possible; otherwise document the verification limit)

**Files involved:** `media_player.spec`, `README.md` (packaging section)

**Dependencies:** US-050, US-051

**Notes for Claude Code:** the main point of caution here is FFmpeg's dynamic linking on macOS — explicitly verify, after packaging, that the FFmpeg libraries are actually bundled inside the `.app` bundle (e.g. via `otool -L` on the final binary) and not merely present on the build machine.

---

### US-061 — Write the final user-facing documentation

**As a** user (or a visitor to the public repository), **I want** a complete README, **so that** I understand how to install, run, and contribute to the project.

**Acceptance criteria:**
- `README.md` contains: a project description, screenshots or a demo GIF, installation instructions (for developers and for end users via the packaged executable), a list of MVP features, the licence (GPLv3, consistent with PyQt6), and a link to this user stories file and the PRD for a curious reader if relevant
- A licence file (`LICENSE`, GPLv3) is present at the repository root

**Files involved:** `README.md`, `LICENSE`

**Dependencies:** US-060

**Notes for Claude Code:** this is the final MVP story — once complete, explicitly check the project's state against the 7 MVP acceptance criteria listed in PRD section 8, one by one, before considering the project "done".
