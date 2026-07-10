# User Stories V2 — Lecteur Audio/Vidéo PyQt6 + QtMultimedia

**Document compagnon de** `PRD_V2_Lecteur_Media_PyQt6.md`
**Prérequis :** toutes les user stories V1 (US-000 à US-061) complétées, MVP packagé et validé
**Usage :** exécution séquentielle par Claude Code, story par story. Les phases 7 à 10 sont indépendantes entre elles (réordonnables) ; les phases 11 et 12 doivent rester en dernier (cf. PRD V2 section 6).

**Convention d'ID :** `US-PPNN` où `PP` = numéro de phase (07 à 12), `NN` = numéro de story dans la phase — dans la continuité numérique des IDs V1.

**Rappel non-négociable (hérité du PRD V2, section 1) :** aucune story de ce document ne doit modifier les assertions des tests V1 existants. Toute évolution de comportement passe par un paramètre à valeur par défaut rétrocompatible. Si une story semble exiger de casser un test V1, s'arrêter et signaler le conflit plutôt que de modifier le test.

---

## Phase 7 — Persistance & réglages

### US-070 — Implémenter la persistance de la playlist

**En tant que** développeur, **je veux** une classe gérant la sérialisation/désérialisation de la playlist vers un fichier JSON dédié, **afin de** permettre à l'utilisateur de retrouver sa playlist après redémarrage (F12 du PRD V2).

**Critères d'acceptation :**
- `core/playlist_persistence.py` définit des fonctions `save_playlist(items: list[MediaItem], path: Path)` et `load_playlist(path: Path) -> list[MediaItem]`
- Le fichier cible est `playlist.json`, distinct de tout futur fichier de préférences (décision actée en PRD V2 section 9)
- `load_playlist()` filtre silencieusement les entrées dont `file_path` n'existe plus sur disque (`Path.exists()`), sans lever d'exception
- Un test `tests/test_playlist_persistence.py` couvre : sauvegarde puis rechargement identique, fichier absent (retourne une liste vide), fichier JSON corrompu (retourne une liste vide sans crash), entrée avec fichier manquant (filtrée silencieusement)

**Fichiers concernés :** `core/playlist_persistence.py`, `tests/test_playlist_persistence.py`

**Dépendances :** US-011 (modèles `MediaItem`)

**Notes pour Claude Code :** ce module ne dépend d'aucun widget — respecter la même discipline `core/` que dans le MVP. Utiliser `json.dumps`/`json.loads` avec un encodage explicite `MediaItem` (ex. via `dataclasses.asdict` côté écriture, reconstruction manuelle côté lecture pour gérer la conversion `str` → `Path`).

---

### US-071 — Intégrer la sauvegarde/chargement automatique de la playlist

**En tant qu'**utilisateur, **je veux** que ma playlist se sauvegarde automatiquement et se recharge au lancement, **afin de** ne pas avoir à reconstituer ma liste de lecture à chaque session.

**Critères d'acceptation :**
- `PlaylistManager` (ou le `PlayerViewModel`) déclenche `save_playlist()` après chaque `add()`/`remove()`, pas uniquement à la fermeture de l'application
- `main.py` (ou l'initialisation de `MainWindow`) appelle `load_playlist()` au démarrage et peuple la playlist en conséquence
- Si un ou plusieurs fichiers ont été filtrés silencieusement (déplacés/supprimés depuis la dernière session), un message discret (pas une boîte de dialogue bloquante) informe l'utilisateur du nombre de fichiers manquants

**Fichiers concernés :** `core/playlist_manager.py`, `viewmodels/player_viewmodel.py`, `ui/main_window.py`

**Dépendances :** US-070

**Notes pour Claude Code :** vérifier explicitement que le test V1 existant `tests/test_playlist_manager.py` passe toujours sans modification — `PlaylistManager` gagne une dépendance à la persistance, mais son comportement `next()`/`previous()`/`add()`/`remove()` ne doit pas changer.

---

## Phase 8 — Vitesse, plein écran & thème

### US-080 — Implémenter le gestionnaire de préférences

**En tant que** développeur, **je veux** un mécanisme générique de sauvegarde des préférences utilisateur, **afin de** disposer d'un socle réutilisable par F15 (thème) et par les fonctionnalités futures nécessitant de la persistance de réglages.

**Critères d'acceptation :**
- `core/settings_manager.py` définit une classe ou des fonctions permettant de lire/écrire des paires clé-valeur simples vers `settings.json` (fichier distinct de `playlist.json`, décision actée en PRD V2 section 9)
- Valeurs par défaut sensées si `settings.json` n'existe pas encore (premier lancement)
- Un test `tests/test_settings_manager.py` couvre : écriture puis lecture identique, fichier absent (valeurs par défaut), fichier corrompu (valeurs par défaut sans crash)

**Fichiers concernés :** `core/settings_manager.py`, `tests/test_settings_manager.py`

**Dépendances :** aucune (indépendant de `playlist_persistence.py`)

**Notes pour Claude Code :** garder une API volontairement simple (get/set par clé), sans sur-ingénierie — ce composant sert F15 dans cette phase, mais aussi implicitement le "dernier volume" mentionné dans les critères d'acceptation du PRD V2 (section 7), à prévoir dès maintenant comme clé possible même si son câblage complet n'est pas exigé dans cette story.

---

### US-081 — Implémenter le contrôle de vitesse de lecture

**En tant qu'**utilisateur, **je veux** ajuster la vitesse de lecture entre 0.5x et 2x, **afin de** accélérer ou ralentir la lecture selon mes besoins (F18 du PRD V2).

**Critères d'acceptation :**
- `core/player_engine.py` gagne une méthode `set_playback_rate(rate: float)` déléguant à `QMediaPlayer.setPlaybackRate()`, avec validation de la plage (0.5 à 2.0 ; valeur hors plage rejetée ou clampée, comportement à choisir et documenter)
- Un contrôle UI (menu déroulant ou slider discret avec paliers, ex. 0.5x/0.75x/1x/1.25x/1.5x/2x) déclenche ce changement via le ViewModel
- Un test `tests/test_player_engine.py` (étendu) vérifie que `set_playback_rate()` avec une valeur valide met bien à jour l'état interne, et qu'une valeur hors plage est gérée sans exception

**Fichiers concernés :** `core/player_engine.py`, `ui/controls_widget.py`, `tests/test_player_engine.py`

**Dépendances :** US-020 (V1)

**Notes pour Claude Code :** story la plus simple de la V2, purement additive — aucun impact sur les tests V1 existants attendu ici, à confirmer néanmoins par exécution complète de la suite de tests avant de committer.

---

### US-082 — Implémenter le mode plein écran

**En tant qu'**utilisateur, **je veux** basculer la fenêtre en plein écran via double-clic sur la vidéo ou raccourci clavier, **afin de** profiter d'une expérience de visionnage immersive (F20 du PRD V2).

**Critères d'acceptation :**
- Double-clic sur `QVideoWidget` bascule `MainWindow` entre `showFullScreen()` et `showNormal()`
- `Échap` sort du plein écran s'il est actif
- Scope volontairement minimal (décision actée en PRD V2 section 3.9) : pas de masquage automatique des contrôles après inactivité de la souris dans cette story — les contrôles restent visibles en plein écran pour le MVP V2
- Si le mini-mode (US-100/US-101) est actif au moment de la bascule plein écran, le comportement doit être défini explicitement (recommandation : désactiver le plein écran depuis le mini-mode, ou le traiter comme incompatible avec un message clair) plutôt que de laisser un état ambigu

**Fichiers concernés :** `ui/main_window.py`

**Dépendances :** US-021 (V1)

**Notes pour Claude Code :** si cette story est développée avant US-100/US-101 (Phase 10), la clause d'interaction avec le mini-mode ne peut pas encore être implémentée — la documenter comme TODO explicite dans le code (`# TODO(US-101): define fullscreen behaviour when mini-mode is active`) plutôt que de l'ignorer silencieusement.

---

### US-083 — Implémenter le thème sombre/clair

**En tant qu'**utilisateur, **je veux** basculer entre un thème sombre et un thème clair, avec mon choix mémorisé, **afin de** personnaliser l'apparence de l'application (F15 du PRD V2).

**Critères d'acceptation :**
- `ui/theme_manager.py` applique une feuille de style Qt (QSS) selon le thème sélectionné (au minimum deux feuilles de style : `dark.qss`, `light.qss`, stockées dans `ui/resources/` ou équivalent)
- Un menu ou bouton bascule entre les deux thèmes
- Le choix est sauvegardé via `settings_manager.py` (US-080) et restauré au démarrage
- Au tout premier lancement (aucune préférence sauvegardée), le thème système macOS est détecté et utilisé comme valeur par défaut plutôt qu'un thème arbitraire

**Fichiers concernés :** `ui/theme_manager.py`, `ui/resources/dark.qss`, `ui/resources/light.qss`, `ui/main_window.py`

**Dépendances :** US-080

**Notes pour Claude Code :** pour la détection du thème système macOS, `QApplication.styleHints()` ou l'inspection de la palette système sont les pistes à explorer en premier — si l'API précise n'est pas triviale à identifier, documenter dans le code la limitation rencontrée plutôt que de deviner un comportement non vérifié.

---

## Phase 9 — Répétition & aléatoire

### US-090 — Étendre le modèle avec l'énumération RepeatMode

**En tant que** développeur, **je veux** une énumération représentant les modes de répétition, **afin de** disposer du vocabulaire nécessaire avant de modifier `PlaylistManager`.

**Critères d'acceptation :**
- `core/models.py` gagne une énumération `RepeatMode` avec au minimum : `NONE`, `TRACK`, `PLAYLIST`
- Aucune classe existante n'est modifiée dans cette story — uniquement un ajout
- Le test V1 existant `tests/test_models.py` passe toujours sans modification

**Fichiers concernés :** `core/models.py`

**Dépendances :** US-011 (V1)

**Notes pour Claude Code :** story volontairement isolée du reste de la logique — sert uniquement à préparer le terrain pour US-091 sans toucher à `PlaylistManager` dans la même story, pour faciliter la revue et le rollback en cas de problème.

---

### US-091 — Implémenter le mode répétition dans PlaylistManager

**En tant qu'**utilisateur, **je veux** pouvoir répéter une piste ou toute la playlist, **afin de** ne pas avoir à relancer manuellement la lecture (F13 du PRD V2).

**Critères d'acceptation :**
- `PlaylistManager.__init__` gagne un paramètre `repeat_mode: RepeatMode = RepeatMode.NONE` (valeur par défaut = comportement V1 actuel, non négociable)
- Avec `repeat_mode = RepeatMode.NONE` : comportement strictement identique à V1 (blocage en fin de liste)
- Avec `repeat_mode = RepeatMode.TRACK` : `next()` recharge le même élément au lieu d'avancer
- Avec `repeat_mode = RepeatMode.PLAYLIST` : `next()` en fin de liste revient au premier élément (bouclage), `previous()` en début de liste revient au dernier
- Une méthode `set_repeat_mode(mode: RepeatMode)` permet de changer le mode en cours d'exécution
- Un contrôle UI (bouton cyclant entre les trois modes, avec icône différenciée) déclenche ce changement via le ViewModel
- **Critère de non-régression explicite :** `pytest tests/test_playlist_manager.py -v` doit afficher exactement les mêmes tests passants qu'en V1, plus les nouveaux tests, sans qu'aucune assertion existante n'ait été modifiée (vérifiable par `git diff` sur ce fichier avant de committer)

**Fichiers concernés :** `core/playlist_manager.py`, `core/models.py` (si `RepeatMode` n'est pas encore présent), `ui/controls_widget.py`, `tests/test_playlist_manager.py` (étendu, jamais modifié dans ses tests existants)

**Dépendances :** US-090

**Notes pour Claude Code :** avant de modifier `playlist_manager.py`, ouvrir `tests/test_playlist_manager.py` et lister explicitement les assertions actuelles concernant `next()`/`previous()` en fin/début de liste — ce sont les lignes qui ne doivent jamais changer. Si l'implémentation naturelle du mode `PLAYLIST` semble nécessiter de changer une de ces assertions, c'est un signal qu'il faut revoir l'implémentation, pas le test.

---

### US-092 — Implémenter le mode aléatoire

**En tant qu'**utilisateur, **je veux** lire la playlist dans un ordre aléatoire, **afin de** varier l'écoute sans réorganiser manuellement mes fichiers (F14 du PRD V2).

**Critères d'acceptation :**
- Un nouvel ordre aléatoire (algorithme de Fisher-Yates recommandé) est calculé une seule fois à l'activation du mode shuffle, pas recalculé à chaque appel de `next()`
- Chaque piste de la playlist n'est jouée qu'une seule fois avant qu'un nouveau cycle aléatoire ne recommence (pas de répétition rapprochée type shuffle naïf)
- Le mode shuffle est compatible avec `repeat_mode` (ex. shuffle + `RepeatMode.PLAYLIST` = nouveau tirage aléatoire à chaque boucle complète)
- Un contrôle UI (bouton toggle) active/désactive le mode shuffle
- Un test `tests/test_playlist_manager.py` (étendu) vérifie que sur N activations de `next()` où N = taille de la playlist, chaque élément apparaît exactement une fois

**Fichiers concernés :** `core/playlist_manager.py` (ou nouveau `core/shuffle_strategy.py` si la logique combinée shuffle + repeat devient complexe — à évaluer en cours d'implémentation), `ui/controls_widget.py`

**Dépendances :** US-091

**Notes pour Claude Code :** même règle de non-régression que US-091 — vérifier `git diff` sur les assertions existantes de `tests/test_playlist_manager.py` avant de committer. Si la complexité combinée shuffle+repeat pousse à extraire `core/shuffle_strategy.py`, mettre à jour le PRD V2 (section 4) pour garder l'architecture documentée synchronisée avec le code réel.

---

## Phase 10 — Mini-mode

### US-100 — Créer la fenêtre mini-mode

**En tant qu'**utilisateur, **je veux** une fenêtre compacte affichant uniquement la vidéo et des contrôles minimalistes, **afin de** regarder du contenu en arrière-plan pendant que je travaille sur autre chose (F19 du PRD V2).

**Critères d'acceptation :**
- `ui/mini_mode_window.py` définit une classe `MiniModeWindow(QWidget)` avec : zone vidéo, boutons play/pause, bouton de fermeture/retour au mode normal
- La fenêtre a l'attribut always-on-top (`Qt.WindowType.WindowStaysOnTopHint`)
- `MiniModeWindow` s'abonne au **même** `PlayerViewModel` que `MainWindow` — aucune nouvelle instance de `PlayerEngine` n'est créée
- Un bouton/raccourci dans `MainWindow` bascule vers `MiniModeWindow` (masque la fenêtre principale, affiche la mini-fenêtre)

**Fichiers concernés :** `ui/mini_mode_window.py`, `ui/main_window.py`

**Dépendances :** US-023 (V1, `PlayerViewModel`)

**Notes pour Claude Code :** c'est la story qui valide (ou invalide) le pattern MVVM du PRD V1 — si l'implémentation naturelle pousse à dupliquer un état déjà présent dans `PlayerViewModel` plutôt qu'à s'y abonner, s'arrêter et signaler explicitement quelle partie du ViewModel V1 semble mal exposée, plutôt que de contourner le problème par une solution ad hoc dans `MiniModeWindow`.

---

### US-101 — Synchroniser bidirectionnellement fenêtre principale et mini-mode

**En tant qu'**utilisateur, **je veux** que les actions dans un mode se reflètent immédiatement dans l'autre, **afin de** ne jamais avoir un état de lecture incohérent entre les deux fenêtres.

**Critères d'acceptation :**
- Play/pause depuis `MiniModeWindow` met à jour l'état visible si l'utilisateur revient à `MainWindow`, et vice-versa
- La position de lecture, le volume, et le média en cours restent cohérents entre les deux vues à tout moment
- Le comportement du plein écran (US-082) vis-à-vis du mini-mode est maintenant tranché ici (résolution du TODO laissé en US-082) : décision à documenter explicitement en commentaire dans le code
- Un test `tests/test_ui_integration.py` (étendu) simule une action dans `MiniModeWindow` via `qtbot` et vérifie que l'état exposé par `PlayerViewModel` (donc visible depuis `MainWindow`) est cohérent

**Fichiers concernés :** `ui/mini_mode_window.py`, `ui/main_window.py`, `viewmodels/player_viewmodel.py` (si un ajustement de signal est nécessaire), `tests/test_ui_integration.py`

**Dépendances :** US-100, US-082

**Notes pour Claude Code :** résoudre explicitement le `TODO(US-101)` laissé dans `ui/main_window.py` par US-082 — ne pas le laisser traîner dans le code une fois cette story terminée.

---

## Phase 11 — Miniatures

### US-110 — Étendre le packaging PyInstaller pour bundler ffmpeg

**En tant que** développeur, **je veux** que le binaire `ffmpeg` soit inclus dans l'exécutable packagé, **afin de** permettre la génération de miniatures sans dépendance système externe non documentée (conséquence de la décision actée en PRD V2 section 9 point 2).

**Critères d'acceptation :**
- Le fichier de spec PyInstaller (`media_player.spec`, créé en V1 US-060) est étendu pour inclure le binaire `ffmpeg` (via `binaries=[...]` dans la spec)
- Après packaging, l'exécutable `.app` contient bien le binaire `ffmpeg` dans son bundle (vérifiable via inspection du contenu du `.app`, ex. `find MediaPlayer.app -name ffmpeg`)
- Un appel à `ffmpeg` depuis l'application packagée fonctionne sur une machine sans `ffmpeg` installé système (si possible à vérifier ; sinon documenter la limite de vérification, cohérent avec la note de US-060 en V1)
- La taille de l'exécutable avant/après cette story est mesurée et documentée dans le README (exigence non fonctionnelle du PRD V2, section 5)

**Fichiers concernés :** `media_player.spec`, `README.md`

**Dépendances :** US-060 (V1)

**Notes pour Claude Code :** cette story doit être terminée **avant** US-111 — générer des miniatures en développement local avec un `ffmpeg` système installé peut fonctionner alors que l'exécutable packagé échoue silencieusement en l'absence de ce binaire bundlé. Tester spécifiquement le binaire packagé, pas uniquement l'environnement de développement.

---

### US-111 — Implémenter la génération de miniatures via ffmpeg

**En tant que** développeur, **je veux** une classe extrayant une frame représentative d'un fichier vidéo via `ffmpeg` en sous-processus, **afin de** fournir des miniatures pour la playlist (F16 du PRD V2).

**Critères d'acceptation :**
- `core/thumbnail_generator.py` définit une fonction ou classe `generate_thumbnail(media_item: MediaItem, cache_dir: Path) -> Path | None`
- L'extraction utilise `subprocess.run()` avec un timeout explicite (ex. 10 secondes) pour éviter un blocage indéfini sur un fichier problématique
- La frame est extraite à une position relative de la durée (ex. 10%), pas à la position 0 (souvent un écran noir en début de vidéo)
- En cas d'échec (fichier corrompu, timeout, `ffmpeg` retourne un code d'erreur), la fonction retourne `None` sans lever d'exception non gérée — dégradation gracieuse vers une icône générique côté UI (US-112)
- Les miniatures générées sont mises en cache sur disque (`~/Library/Caches/MediaPlayer/thumbnails/`, nommage basé sur un hash du chemin du fichier source) pour éviter une régénération à chaque lancement
- Un test `tests/test_thumbnail_generator.py` couvre : extraction réussie sur un fichier de test, fichier inexistant, timeout simulé, vérification que le cache est bien utilisé au second appel

**Fichiers concernés :** `core/thumbnail_generator.py`, `tests/test_thumbnail_generator.py`

**Dépendances :** US-110

**Notes pour Claude Code :** invoquer `ffmpeg` avec des arguments explicites et éviter `shell=True` dans `subprocess.run()` (passer une liste d'arguments) pour éviter tout risque d'injection de commande si un nom de fichier contient des caractères spéciaux.

---

### US-112 — Afficher les miniatures dans la playlist

**En tant qu'**utilisateur, **je veux** voir un aperçu visuel de chaque vidéo dans ma playlist, **afin de** identifier plus rapidement mes fichiers.

**Critères d'acceptation :**
- `ui/playlist_widget.py` affiche la miniature générée (US-111) à côté de `display_name` pour chaque élément vidéo
- Pendant la génération (potentiellement asynchrone, cf. exigence non fonctionnelle du PRD V2 section 5), une icône de chargement ou un placeholder neutre s'affiche à la place
- Si `generate_thumbnail()` retourne `None`, une icône générique (ex. icône de fichier vidéo générique) s'affiche sans erreur visible pour l'utilisateur
- Les fichiers purement audio (sans piste vidéo) affichent une icône dédiée (ex. icône de note de musique), pas une tentative d'extraction de miniature

**Fichiers concernés :** `ui/playlist_widget.py`

**Dépendances :** US-111

**Notes pour Claude Code :** la génération de miniatures doit être asynchrone (ex. `QThreadPool` avec un `QRunnable` par fichier) pour respecter l'exigence de non-blocage de l'UI du PRD V2 (section 5) — ne pas appeler `generate_thumbnail()` de manière synchrone dans le thread principal lors du peuplement de la playlist.

---

### US-113 — Valider la robustesse sous charge

**En tant que** développeur, **je veux** vérifier que la génération de miniatures reste stable sur un grand nombre de fichiers, **afin de** m'assurer que le choix architectural de F16 (sous-processus `ffmpeg`) tient la charge avant de considérer la fonctionnalité terminée.

**Critères d'acceptation :**
- Un test (manuel ou automatisé) génère des miniatures pour une playlist d'au moins 20 fichiers vidéo différents (formats variés si possible : MP4, MKV, WebM)
- Aucun processus `ffmpeg` zombie ne reste actif après la génération complète (vérifiable via `ps aux | grep ffmpeg` après exécution)
- Le temps cumulé de génération pour 20 fichiers reste dans un ordre de grandeur raisonnable (à documenter avec une valeur mesurée réelle, pas une estimation)
- Les résultats de ce test sont documentés dans un fichier `docs/V2_LOAD_TEST_NOTES.md` (nombre de fichiers, temps total, échecs éventuels et leur cause)

**Fichiers concernés :** `docs/V2_LOAD_TEST_NOTES.md`

**Dépendances :** US-112

**Notes pour Claude Code :** cette story est une validation, pas une fonctionnalité — si le test révèle un problème (fuite de processus, lenteur excessive), documenter le problème précisément dans `V2_LOAD_TEST_NOTES.md` et ouvrir une nouvelle story de correction plutôt que de modifier silencieusement US-111 sans traçabilité.

---

## Phase 12 — Sous-titres

### US-120 — Implémenter le parseur de sous-titres SRT

**En tant que** développeur, **je veux** une fonction parsant un fichier `.srt` en une structure de données exploitable, **afin de** préparer l'affichage synchronisé des sous-titres (F17 du PRD V2).

**Critères d'acceptation :**
- `core/subtitle_parser.py` définit une fonction `parse_srt(path: Path) -> list[SubtitleEntry]`, avec `SubtitleEntry` une dataclass dans `core/models.py` (`start_ms: int`, `end_ms: int`, `text: str`)
- Le parseur gère les deux encodages les plus courants (UTF-8, Latin-1/Windows-1252), avec détection ou repli automatique
- Un fichier `.srt` malformé (syntaxe invalide, timecodes incohérents) ne lève pas d'exception non gérée — retourne une liste vide ou partielle avec le contenu valide récupérable
- Un test `tests/test_subtitle_parser.py` couvre : fichier `.srt` valide standard, fichier avec encodage Latin-1, fichier malformé, fichier vide, fichier inexistant

**Fichiers concernés :** `core/subtitle_parser.py`, `core/models.py` (ajout `SubtitleEntry`), `tests/test_subtitle_parser.py`

**Dépendances :** US-011 (V1)

**Notes pour Claude Code :** ne pas utiliser de bibliothèque tierce lourde pour un format aussi simple que `.srt` — un parseur manuel avec des expressions régulières ciblées est suffisant et évite d'alourdir `requirements.txt` pour une fonctionnalité isolée.

---

### US-121 — Créer le widget de superposition des sous-titres

**En tant que** développeur, **je veux** un widget affichant du texte en surimpression sur la vidéo, **afin de** disposer du composant visuel nécessaire à l'affichage des sous-titres.

**Critères d'acceptation :**
- `ui/subtitle_overlay.py` définit un `QLabel` (ou widget équivalent) positionné en surimpression sur `QVideoWidget`, dans le tiers inférieur de la zone vidéo
- Le texte est lisible sur fond vidéo variable (fond semi-transparent derrière le texte, ou contour/ombre portée sur le texte)
- Le widget expose une méthode `set_text(text: str)` et `clear()`
- Le widget se redimensionne/repositionne correctement quand `MainWindow` change de taille ou bascule en plein écran (US-082)

**Fichiers concernés :** `ui/subtitle_overlay.py`, `ui/video_widget.py` (intégration)

**Dépendances :** US-022 (V1, `QVideoWidget`)

**Notes pour Claude Code :** ce widget ne connaît rien du contenu des sous-titres ni de la synchronisation temporelle — il expose uniquement une API d'affichage de texte, la logique de synchronisation vit dans US-122 côté ViewModel.

---

### US-122 — Synchroniser l'affichage des sous-titres avec la lecture

**En tant qu'**utilisateur, **je veux** charger un fichier `.srt` et voir les sous-titres s'afficher synchronisés avec la vidéo, **afin de** suivre du contenu dans une langue que je ne maîtrise pas parfaitement.

**Critères d'acceptation :**
- Un menu ou bouton "Charger les sous-titres" ouvre un dialogue de sélection de fichier `.srt`
- `PlayerViewModel` écoute `positionChanged` et détermine l'entrée `SubtitleEntry` correspondante (si `start_ms <= position <= end_ms` pour une entrée), avec une tolérance de synchronisation de quelques centaines de ms
- `SubtitleOverlay.set_text()` est appelé quand l'entrée active change, `clear()` quand aucune entrée n'est active
- Si le fichier `.srt` chargé est malformé (résultat vide de `parse_srt()`), un message discret informe l'utilisateur sans bloquer la lecture vidéo (dégradation gracieuse conforme au PRD V2 section 5)
- Un test `tests/test_ui_integration.py` (étendu) simule une progression de position et vérifie que le texte affiché correspond à l'entrée attendue à différents instants

**Fichiers concernés :** `viewmodels/player_viewmodel.py`, `ui/main_window.py`, `tests/test_ui_integration.py`

**Dépendances :** US-120, US-121

**Notes pour Claude Code :** dernière story du plan V2 — une fois complétée, comparer explicitement l'état du projet aux 10 critères d'acceptation de la V2 listés en section 7 du PRD V2, un par un, avant de considérer la V2 "terminée". Vérifier également qu'aucun `TODO` résiduel (ex. celui d'US-082) n'a été oublié en cours de route.

---
---

# User Stories V2 (English) — Audio/Video Player, PyQt6 + QtMultimedia

**Companion document to** `PRD_V2_Lecteur_Media_PyQt6.md`
**Prerequisite:** all V1 user stories (US-000 through US-061) completed, MVP packaged and validated
**Usage:** sequential execution by Claude Code, story by story. Phases 7 through 10 are independent of one another (reorderable); Phases 11 and 12 must remain last (see PRD V2 section 6).

**ID convention:** `US-PPNN` where `PP` = phase number (07 to 12), `NN` = story number within the phase — continuing the numeric sequence of the V1 IDs.

**Non-negotiable reminder (inherited from PRD V2, section 1):** no story in this document may modify the assertions of existing V1 tests. Any behavioural change goes through a new, backward-compatible default-valued parameter. If a story appears to require breaking a V1 test, stop and flag the conflict rather than modifying the test.

---

## Phase 7 — Persistence & settings

### US-070 — Implement playlist persistence

**As a** developer, **I want** a class handling serialisation/deserialisation of the playlist to/from a dedicated JSON file, **so that** the user can retrieve their playlist after restarting the application (PRD V2 F12).

**Acceptance criteria:**
- `core/playlist_persistence.py` defines `save_playlist(items: list[MediaItem], path: Path)` and `load_playlist(path: Path) -> list[MediaItem]` functions
- The target file is `playlist.json`, kept separate from any future preferences file (decision made in PRD V2 section 9)
- `load_playlist()` silently filters out entries whose `file_path` no longer exists on disk (`Path.exists()`), without raising an exception
- A `tests/test_playlist_persistence.py` test covers: save then reload producing identical results, a missing file (returns an empty list), a corrupted JSON file (returns an empty list without crashing), an entry with a missing file (silently filtered out)

**Files involved:** `core/playlist_persistence.py`, `tests/test_playlist_persistence.py`

**Dependencies:** US-011 (`MediaItem` model)

**Notes for Claude Code:** this module has no widget dependency — maintain the same `core/` discipline as in the MVP. Use `json.dumps`/`json.loads` with explicit `MediaItem` encoding (e.g. via `dataclasses.asdict` on write, manual reconstruction on read to handle the `str` → `Path` conversion).

---

### US-071 — Wire up automatic playlist save/load

**As a** user, **I want** my playlist to save automatically and reload on launch, **so that** I do not have to rebuild my playlist every session.

**Acceptance criteria:**
- `PlaylistManager` (or `PlayerViewModel`) triggers `save_playlist()` after every `add()`/`remove()`, not only on application exit
- `main.py` (or `MainWindow`'s initialisation) calls `load_playlist()` at startup and populates the playlist accordingly
- If one or more files were silently filtered out (moved/deleted since the last session), a discreet message (not a blocking dialog) informs the user of the number of missing files

**Files involved:** `core/playlist_manager.py`, `viewmodels/player_viewmodel.py`, `ui/main_window.py`

**Dependencies:** US-070

**Notes for Claude Code:** explicitly verify that the existing V1 test `tests/test_playlist_manager.py` still passes unmodified — `PlaylistManager` gains a dependency on persistence, but its `next()`/`previous()`/`add()`/`remove()` behaviour must not change.

---

## Phase 8 — Speed, fullscreen & theme

### US-080 — Implement the preferences manager

**As a** developer, **I want** a generic mechanism for saving user preferences, **so that** F15 (theme) and any future settings-dependent features have a reusable foundation.

**Acceptance criteria:**
- `core/settings_manager.py` defines a class or functions to read/write simple key-value pairs to `settings.json` (a file separate from `playlist.json`, decision made in PRD V2 section 9)
- Sensible default values apply if `settings.json` does not yet exist (first launch)
- A `tests/test_settings_manager.py` test covers: write then read producing identical results, a missing file (defaults), a corrupted file (defaults, no crash)

**Files involved:** `core/settings_manager.py`, `tests/test_settings_manager.py`

**Dependencies:** none (independent of `playlist_persistence.py`)

**Notes for Claude Code:** keep the API deliberately simple (get/set by key), avoiding over-engineering — this component serves F15 in this phase, but also implicitly the "last volume level" mentioned in the PRD V2 acceptance criteria (section 7), which should be anticipated as a possible key now even though its full wiring is not required in this story.

---

### US-081 — Implement playback speed control

**As a** user, **I want** to adjust playback speed between 0.5x and 2x, **so that** I can speed up or slow down playback as needed (PRD V2 F18).

**Acceptance criteria:**
- `core/player_engine.py` gains a `set_playback_rate(rate: float)` method delegating to `QMediaPlayer.setPlaybackRate()`, with range validation (0.5 to 2.0; out-of-range values are either rejected or clamped — behaviour to be chosen and documented)
- A UI control (a dropdown, or a stepped slider, e.g. 0.5x/0.75x/1x/1.25x/1.5x/2x) triggers this change via the ViewModel
- A `tests/test_player_engine.py` test (extended) verifies that `set_playback_rate()` with a valid value correctly updates the internal state, and that an out-of-range value is handled without an exception

**Files involved:** `core/player_engine.py`, `ui/controls_widget.py`, `tests/test_player_engine.py`

**Dependencies:** US-020 (V1)

**Notes for Claude Code:** the simplest, purely additive story in V2 — no impact on existing V1 tests is expected here, though this should still be confirmed by running the full test suite before committing.

---

### US-082 — Implement fullscreen mode

**As a** user, **I want** to switch the window to fullscreen via a double-click on the video or a keyboard shortcut, **so that** I get an immersive viewing experience (PRD V2 F20).

**Acceptance criteria:**
- Double-clicking `QVideoWidget` toggles `MainWindow` between `showFullScreen()` and `showNormal()`
- `Escape` exits fullscreen if active
- Deliberately minimal scope (decision made in PRD V2 section 3.9): no automatic control-hiding after mouse inactivity in this story — controls remain visible in fullscreen for the V2 MVP
- If mini-mode (US-100/US-101) is active when fullscreen is toggled, the behaviour must be explicitly defined (recommendation: disable fullscreen from mini-mode, or treat it as incompatible with a clear message) rather than leaving an ambiguous state

**Files involved:** `ui/main_window.py`

**Dependencies:** US-021 (V1)

**Notes for Claude Code:** if this story is developed before US-100/US-101 (Phase 10), the mini-mode interaction clause cannot yet be implemented — document it as an explicit TODO in the code (`# TODO(US-101): define fullscreen behaviour when mini-mode is active`) rather than silently ignoring it.

---

### US-083 — Implement the dark/light theme

**As a** user, **I want** to switch between a dark and a light theme, with my choice remembered, **so that** I can personalise the application's appearance (PRD V2 F15).

**Acceptance criteria:**
- `ui/theme_manager.py` applies a Qt stylesheet (QSS) according to the selected theme (at least two stylesheets: `dark.qss`, `light.qss`, stored under `ui/resources/` or equivalent)
- A menu or button toggles between the two themes
- The choice is saved via `settings_manager.py` (US-080) and restored on startup
- On the very first launch (no saved preference), the macOS system theme is detected and used as the default, rather than an arbitrary theme

**Files involved:** `ui/theme_manager.py`, `ui/resources/dark.qss`, `ui/resources/light.qss`, `ui/main_window.py`

**Dependencies:** US-080

**Notes for Claude Code:** for macOS system theme detection, `QApplication.styleHints()` or inspecting the system palette are the first avenues to explore — if the precise API is not trivial to pin down, document the limitation encountered in the code rather than guessing at unverified behaviour.

---

## Phase 9 — Repeat & shuffle

### US-090 — Extend the model with the RepeatMode enum

**As a** developer, **I want** an enum representing the repeat modes, **so that** the vocabulary is in place before modifying `PlaylistManager`.

**Acceptance criteria:**
- `core/models.py` gains a `RepeatMode` enum with at least: `NONE`, `TRACK`, `PLAYLIST`
- No existing class is modified in this story — addition only
- The existing V1 test `tests/test_models.py` still passes unmodified

**Files involved:** `core/models.py`

**Dependencies:** US-011 (V1)

**Notes for Claude Code:** this story is deliberately isolated from the rest of the logic — its only purpose is to prepare the ground for US-091 without touching `PlaylistManager` in the same story, to make review and rollback easier if something goes wrong.

---

### US-091 — Implement repeat mode in PlaylistManager

**As a** user, **I want** to be able to repeat a track or the whole playlist, **so that** I do not have to manually restart playback (PRD V2 F13).

**Acceptance criteria:**
- `PlaylistManager.__init__` gains a `repeat_mode: RepeatMode = RepeatMode.NONE` parameter (default value = current V1 behaviour, non-negotiable)
- With `repeat_mode = RepeatMode.NONE`: behaviour strictly identical to V1 (stops at the end of the list)
- With `repeat_mode = RepeatMode.TRACK`: `next()` reloads the same item instead of advancing
- With `repeat_mode = RepeatMode.PLAYLIST`: `next()` at the end of the list wraps to the first item, `previous()` at the start wraps to the last
- A `set_repeat_mode(mode: RepeatMode)` method allows changing the mode at runtime
- A UI control (a button cycling through the three modes, with a distinct icon per mode) triggers this change via the ViewModel
- **Explicit non-regression criterion:** `pytest tests/test_playlist_manager.py -v` must show exactly the same passing tests as in V1, plus the new tests, with no existing assertion modified (verifiable via `git diff` on this file before committing)

**Files involved:** `core/playlist_manager.py`, `core/models.py` (if `RepeatMode` is not already present), `ui/controls_widget.py`, `tests/test_playlist_manager.py` (extended, never modified in its existing tests)

**Dependencies:** US-090

**Notes for Claude Code:** before modifying `playlist_manager.py`, open `tests/test_playlist_manager.py` and explicitly list the current assertions concerning `next()`/`previous()` at the start/end of the list — these are the lines that must never change. If the natural implementation of `PLAYLIST` mode appears to require changing one of these assertions, that is a signal to revisit the implementation, not the test.

---

### US-092 — Implement shuffle mode

**As a** user, **I want** to play the playlist in random order, **so that** I can vary my listening without manually reorganising my files (PRD V2 F14).

**Acceptance criteria:**
- A new random order (Fisher–Yates shuffle recommended) is computed once when shuffle mode is activated, not recomputed on every `next()` call
- Each track in the playlist plays exactly once before a new random cycle begins (no naive-shuffle close repeats)
- Shuffle mode is compatible with `repeat_mode` (e.g. shuffle + `RepeatMode.PLAYLIST` = a fresh random draw on every full loop)
- A UI control (a toggle button) enables/disables shuffle mode
- A `tests/test_playlist_manager.py` test (extended) verifies that across N calls to `next()`, where N = playlist size, each item appears exactly once

**Files involved:** `core/playlist_manager.py` (or a new `core/shuffle_strategy.py` if the combined shuffle+repeat logic becomes complex — to be assessed during implementation), `ui/controls_widget.py`

**Dependencies:** US-091

**Notes for Claude Code:** the same non-regression rule as US-091 applies — check `git diff` against the existing assertions in `tests/test_playlist_manager.py` before committing. If the combined shuffle+repeat complexity pushes towards extracting `core/shuffle_strategy.py`, update the PRD V2 (section 4) to keep the documented architecture in sync with the actual code.

---

## Phase 10 — Mini-mode

### US-100 — Create the mini-mode window

**As a** user, **I want** a compact window showing only the video and minimal controls, **so that** I can watch content in the background while working on something else (PRD V2 F19).

**Acceptance criteria:**
- `ui/mini_mode_window.py` defines a `MiniModeWindow(QWidget)` class with: a video area, play/pause buttons, a close/return-to-normal-mode button
- The window has the always-on-top attribute (`Qt.WindowType.WindowStaysOnTopHint`)
- `MiniModeWindow` subscribes to the **same** `PlayerViewModel` as `MainWindow` — no new `PlayerEngine` instance is created
- A button/shortcut in `MainWindow` switches to `MiniModeWindow` (hides the main window, shows the mini window)

**Files involved:** `ui/mini_mode_window.py`, `ui/main_window.py`

**Dependencies:** US-023 (V1, `PlayerViewModel`)

**Notes for Claude Code:** this story validates (or invalidates) the V1 PRD's MVVM pattern — if the natural implementation pushes towards duplicating state already present in `PlayerViewModel` rather than subscribing to it, stop and explicitly flag which part of the V1 ViewModel appears poorly exposed, rather than working around the issue with an ad hoc solution inside `MiniModeWindow`.

---

### US-101 — Bidirectionally synchronise the main window and mini-mode

**As a** user, **I want** actions in one mode to be reflected immediately in the other, **so that** I never see an inconsistent playback state between the two windows.

**Acceptance criteria:**
- Play/pause from `MiniModeWindow` updates the visible state when returning to `MainWindow`, and vice versa
- Playback position, volume, and the current media item remain consistent between both views at all times
- Fullscreen's (US-082) behaviour with respect to mini-mode is now settled here (resolving the TODO left in US-082): the decision must be documented explicitly as a code comment
- A `tests/test_ui_integration.py` test (extended) simulates an action in `MiniModeWindow` via `qtbot` and verifies that the state exposed by `PlayerViewModel` (and thus visible from `MainWindow`) is consistent

**Files involved:** `ui/mini_mode_window.py`, `ui/main_window.py`, `viewmodels/player_viewmodel.py` (if a signal adjustment is needed), `tests/test_ui_integration.py`

**Dependencies:** US-100, US-082

**Notes for Claude Code:** explicitly resolve the `TODO(US-101)` left in `ui/main_window.py` by US-082 — do not leave it lingering in the code once this story is complete.

---

## Phase 11 — Thumbnails

### US-110 — Extend PyInstaller packaging to bundle ffmpeg

**As a** developer, **I want** the `ffmpeg` binary bundled into the packaged executable, **so that** thumbnail generation works without an undocumented external system dependency (a consequence of the decision made in PRD V2 section 9, point 2).

**Acceptance criteria:**
- The PyInstaller spec file (`media_player.spec`, created in V1 US-060) is extended to include the `ffmpeg` binary (via `binaries=[...]` in the spec)
- After packaging, the `.app` executable actually contains the `ffmpeg` binary in its bundle (verifiable by inspecting the `.app`'s contents, e.g. `find MediaPlayer.app -name ffmpeg`)
- Calling `ffmpeg` from the packaged application works on a machine without a system-level `ffmpeg` install (verify if possible; otherwise document the verification limit, consistent with the US-060 note from V1)
- The executable's size before/after this story is measured and documented in the README (PRD V2 non-functional requirement, section 5)

**Files involved:** `media_player.spec`, `README.md`

**Dependencies:** US-060 (V1)

**Notes for Claude Code:** this story must be completed **before** US-111 — generating thumbnails in local development with a system-installed `ffmpeg` may work even though the packaged executable silently fails without the bundled binary. Specifically test the packaged binary, not just the development environment.

---

### US-111 — Implement thumbnail generation via ffmpeg

**As a** developer, **I want** a class extracting a representative frame from a video file via `ffmpeg` as a subprocess, **so that** thumbnails are available for the playlist (PRD V2 F16).

**Acceptance criteria:**
- `core/thumbnail_generator.py` defines a `generate_thumbnail(media_item: MediaItem, cache_dir: Path) -> Path | None` function or class
- Extraction uses `subprocess.run()` with an explicit timeout (e.g. 10 seconds) to avoid an indefinite hang on a problematic file
- The frame is extracted at a position relative to the duration (e.g. 10%), not at position 0 (often a black screen at the start of a video)
- On failure (corrupted file, timeout, `ffmpeg` returning an error code), the function returns `None` without raising an unhandled exception — graceful degradation to a generic icon on the UI side (US-112)
- Generated thumbnails are cached on disk (`~/Library/Caches/MediaPlayer/thumbnails/`, named using a hash of the source file's path) to avoid regeneration on every launch
- A `tests/test_thumbnail_generator.py` test covers: successful extraction on a test file, a non-existent file, a simulated timeout, and confirmation that the cache is actually used on the second call

**Files involved:** `core/thumbnail_generator.py`, `tests/test_thumbnail_generator.py`

**Dependencies:** US-110

**Notes for Claude Code:** invoke `ffmpeg` with explicit arguments and avoid `shell=True` in `subprocess.run()` (pass a list of arguments) to avoid any command-injection risk should a filename contain special characters.

---

### US-112 — Display thumbnails in the playlist

**As a** user, **I want** to see a visual preview of each video in my playlist, **so that** I can identify my files more quickly.

**Acceptance criteria:**
- `ui/playlist_widget.py` displays the generated thumbnail (US-111) next to `display_name` for each video item
- While generation is in progress (potentially asynchronous, see PRD V2 non-functional requirement, section 5), a loading icon or neutral placeholder is shown instead
- If `generate_thumbnail()` returns `None`, a generic icon (e.g. a generic video-file icon) is shown with no visible error to the user
- Audio-only files (no video track) display a dedicated icon (e.g. a musical note icon), rather than attempting thumbnail extraction

**Files involved:** `ui/playlist_widget.py`

**Dependencies:** US-111

**Notes for Claude Code:** thumbnail generation must be asynchronous (e.g. a `QThreadPool` with one `QRunnable` per file) to meet the PRD V2 non-blocking-UI requirement (section 5) — do not call `generate_thumbnail()` synchronously on the main thread while populating the playlist.

---

### US-113 — Validate robustness under load

**As a** developer, **I want** to verify that thumbnail generation stays stable across a large number of files, **so that** F16's architectural choice (`ffmpeg` subprocess) is confirmed to hold up under load before the feature is considered complete.

**Acceptance criteria:**
- A test (manual or automated) generates thumbnails for a playlist of at least 20 different video files (varied formats where possible: MP4, MKV, WebM)
- No zombie `ffmpeg` processes remain active after generation completes (verifiable via `ps aux | grep ffmpeg` after the run)
- The cumulative generation time for 20 files stays within a reasonable order of magnitude (to be documented with an actual measured value, not an estimate)
- The results of this test are documented in a `docs/V2_LOAD_TEST_NOTES.md` file (number of files, total time, any failures and their cause)

**Files involved:** `docs/V2_LOAD_TEST_NOTES.md`

**Dependencies:** US-112

**Notes for Claude Code:** this story is a validation, not a feature — if the test reveals a problem (process leak, excessive slowness), document the problem precisely in `V2_LOAD_TEST_NOTES.md` and open a new fix story, rather than silently modifying US-111 without traceability.

---

## Phase 12 — Subtitles

### US-120 — Implement the SRT subtitle parser

**As a** developer, **I want** a function parsing an `.srt` file into a usable data structure, **so that** synchronised subtitle display can be built on top of it (PRD V2 F17).

**Acceptance criteria:**
- `core/subtitle_parser.py` defines a `parse_srt(path: Path) -> list[SubtitleEntry]` function, with `SubtitleEntry` a dataclass in `core/models.py` (`start_ms: int`, `end_ms: int`, `text: str`)
- The parser handles the two most common encodings (UTF-8, Latin-1/Windows-1252), with automatic detection or fallback
- A malformed `.srt` file (invalid syntax, inconsistent timecodes) does not raise an unhandled exception — it returns an empty or partial list of recoverable valid content
- A `tests/test_subtitle_parser.py` test covers: a standard valid `.srt` file, a Latin-1-encoded file, a malformed file, an empty file, a non-existent file

**Files involved:** `core/subtitle_parser.py`, `core/models.py` (adding `SubtitleEntry`), `tests/test_subtitle_parser.py`

**Dependencies:** US-011 (V1)

**Notes for Claude Code:** do not pull in a heavy third-party library for a format as simple as `.srt` — a hand-written parser using targeted regular expressions is sufficient and avoids bloating `requirements.txt` for an isolated feature.

---

### US-121 — Create the subtitle overlay widget

**As a** developer, **I want** a widget displaying text overlaid on the video, **so that** the visual component needed for subtitle display is in place.

**Acceptance criteria:**
- `ui/subtitle_overlay.py` defines a `QLabel` (or equivalent widget) positioned as an overlay on `QVideoWidget`, in the lower third of the video area
- The text remains readable against a variable video background (a semi-transparent backdrop behind the text, or an outline/drop shadow on the text)
- The widget exposes a `set_text(text: str)` method and a `clear()` method
- The widget resizes/repositions correctly when `MainWindow` changes size or switches to fullscreen (US-082)

**Files involved:** `ui/subtitle_overlay.py`, `ui/video_widget.py` (integration)

**Dependencies:** US-022 (V1, `QVideoWidget`)

**Notes for Claude Code:** this widget knows nothing about subtitle content or timing synchronisation — it only exposes a text-display API; the synchronisation logic lives in US-122 on the ViewModel side.

---

### US-122 — Synchronise subtitle display with playback

**As a** user, **I want** to load an `.srt` file and see subtitles displayed in sync with the video, **so that** I can follow content in a language I do not fully understand.

**Acceptance criteria:**
- A menu or button "Load subtitles" opens an `.srt` file selection dialog
- `PlayerViewModel` listens to `positionChanged` and determines the matching `SubtitleEntry` (if `start_ms <= position <= end_ms` for an entry), with a synchronisation tolerance of a few hundred milliseconds
- `SubtitleOverlay.set_text()` is called when the active entry changes, and `clear()` when no entry is active
- If the loaded `.srt` file is malformed (an empty result from `parse_srt()`), a discreet message informs the user without blocking video playback (graceful degradation consistent with PRD V2 section 5)
- A `tests/test_ui_integration.py` test (extended) simulates advancing playback position and verifies that the displayed text matches the expected entry at various points in time

**Files involved:** `viewmodels/player_viewmodel.py`, `ui/main_window.py`, `tests/test_ui_integration.py`

**Dependencies:** US-120, US-121

**Notes for Claude Code:** this is the final story of the V2 plan — once complete, explicitly check the project's state against the 10 V2 acceptance criteria listed in PRD V2 section 7, one by one, before considering V2 "done". Also verify that no residual `TODO` (e.g. the one from US-082) was left behind along the way.
