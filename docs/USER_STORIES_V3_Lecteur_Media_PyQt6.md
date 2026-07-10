# User Stories V3 — Lecteur Audio/Vidéo PyQt6 + QtMultimedia (Restylage visuel)

**Document compagnon de** `PRD_V3_Lecteur_Media_PyQt6.md`
**Prérequis :** V1 et V2 complètes
**Usage :** exécution séquentielle par Claude Code. Phase 14 (couleurs) doit précéder Phase 15 (restylage des composants qui consomment la couleur d'accentuation). Phase 13 (plein écran) et Phase 16 (pochette audio) sont indépendantes du reste et réordonnables.

**Convention d'ID :** `US-PPNN`, dans la continuité numérique des IDs V1/V2.

**Rappel non-négociable :** cette V3 est un restylage. Aucune assertion de test V1/V2 existante ne doit être modifiée. Toute story qui semble exiger un changement de comportement fonctionnel (au-delà des deux exceptions `core/` actées dans le PRD V3, section 1) doit s'arrêter et signaler l'écart plutôt que de l'implémenter silencieusement.

---

## Phase 13 — Plein écran overlay

### US-130 — Créer le composant de contrôles superposés

**En tant qu'**utilisateur, **je veux** voir les contrôles de lecture superposés sur la vidéo en plein écran plutôt que dans une barre séparée, **afin de** profiter d'une expérience immersive (F21 du PRD V3).

**Critères d'acceptation :**
- En entrant en plein écran (comportement d'entrée déjà défini en V2 US-082), `ui/controls_widget.py` est repositionné en superposition centrée sur `ui/video_widget.py`, avec un fond semi-transparent, plutôt que dupliqué dans un nouveau widget
- Les boutons affichés en overlay sont identiques fonctionnellement à ceux de la barre normale (mêmes signaux, même ViewModel) — seul le positionnement et le style QSS diffèrent
- En sortant du plein écran, `controls_widget.py` reprend sa position normale (ancré en bas de la fenêtre) sans redémarrage ni réinitialisation d'état

**Fichiers concernés :** `ui/video_widget.py`, `ui/controls_widget.py`, feuilles de style QSS pour le mode overlay

**Dépendances :** US-082 (V2, entrée/sortie du plein écran)

**Notes pour Claude Code :** ne pas créer un second widget de contrôles pour le mode overlay — réutiliser l'instance existante et changer son parent/positionnement selon le mode (normal vs plein écran). Vérifier explicitement que `tests/test_ui_integration.py` (V1/V2) continue de passer sans modification, puisque `controls_widget.py` change de comportement de positionnement mais pas de logique.

### US-131 — Implémenter le masquage automatique par inactivité

**En tant qu'**utilisateur, **je veux** que les contrôles superposés disparaissent après un moment d'inactivité de la souris, **afin de** profiter d'un visionnage sans distraction visuelle (F21 du PRD V3).

**Critères d'acceptation :**
- Un `QTimer` de 5 secondes se réinitialise à chaque `mouseMoveEvent` détecté sur la fenêtre en plein écran
- À l'expiration du timer, les contrôles overlay disparaissent avec un fondu (`QPropertyAnimation` sur `QGraphicsOpacityEffect`, ou repli `hide()` simple si l'animation s'avère instable — décision actée en PRD V3 section 8)
- Tout mouvement de souris après disparition déclenche la réapparition immédiate (fondu d'entrée) et réinitialise le timer
- Si la souris survole directement la zone des contrôles, le timer est suspendu tant qu'elle n'en sort pas
- Si la lecture est en pause, les contrôles restent visibles en permanence, indépendamment du timer

**Fichiers concernés :** `ui/video_widget.py` (gestion du `mouseMoveEvent` et du timer), `ui/controls_widget.py` (état visible/masqué)

**Dépendances :** US-130

**Notes pour Claude Code :** vérifier le comportement pause explicitement en premier (cas le plus simple : timer désactivé), avant de coder la logique de suspension au survol qui est plus subtile (distinction entre "souris immobile sur les contrôles" et "souris immobile ailleurs sur la vidéo").

---

## Phase 14 — Système de couleurs

### US-140 — Étendre le thème avec une couleur d'accentuation

**En tant que** développeur, **je veux** un mécanisme centralisé de couleur d'accentuation, **afin de** permettre aux composants restylés des phases suivantes de s'y référencer de façon cohérente (F25 du PRD V3).

**Critères d'acceptation :**
- `ui/theme_manager.py` (V2) gagne une notion de couleur d'accentuation, choisie parmi une palette prédéfinie (au moins 4-5 couleurs, ex. bleu, violet, vert, orange, rouge)
- Les feuilles de style `dark.qss`/`light.qss` utilisent une variable de couleur d'accentuation injectée dynamiquement (via substitution de chaîne dans le QSS généré, `QPalette`, ou équivalent) plutôt qu'une couleur codée en dur
- Le choix de couleur d'accentuation est persisté via `core/settings_manager.py` (V2), clé distincte de la clé de thème sombre/clair
- Un test `tests/test_theme_manager.py` (étendu si existant, sinon créé) vérifie que changer la couleur d'accentuation modifie effectivement la valeur injectée dans la feuille de style générée

**Fichiers concernés :** `ui/theme_manager.py`, `ui/resources/dark.qss`, `ui/resources/light.qss`

**Dépendances :** US-083 (V2, thème sombre/clair)

**Notes pour Claude Code :** ne pas encore câbler de contrôle UI pour choisir la couleur dans cette story — elle prépare uniquement le mécanisme. Le contrôle utilisateur est ajouté en US-141.

### US-141 — Ajouter le sélecteur de couleur d'accentuation dans les paramètres

**En tant qu'**utilisateur, **je veux** choisir ma couleur d'accentuation depuis les paramètres, **afin de** personnaliser l'apparence de l'application.

**Critères d'acceptation :**
- Le composant de paramètres existant (V2 F15) gagne un contrôle (ex. rangée de pastilles de couleur cliquables) permettant de sélectionner une couleur parmi la palette définie en US-140
- La sélection s'applique immédiatement à l'interface, sans redémarrage de l'application
- Le choix persiste après redémarrage (via `settings_manager.py`, US-140)

**Fichiers concernés :** composant de paramètres existant (V2 F15)

**Dépendances :** US-140

**Notes pour Claude Code :** cette story peut sembler chevaucher F24 (Phase 15, restylage complet des paramètres) — c'est voulu : US-141 ajoute la fonctionnalité minimale au composant existant tel quel, US-152 (Phase 15) restylera l'ensemble du composant de paramètres autour de cette fonctionnalité, pas l'inverse.

---

## Phase 15 — Restylage des composants

### US-150 — Restyler la barre de lecture

**En tant qu'**utilisateur, **je veux** une barre de lecture visuellement soignée et cohérente avec la couleur d'accentuation choisie, **afin de** profiter d'une interface plus agréable (F22 du PRD V3).

**Critères d'acceptation :**
- Bouton play/pause : forme circulaire, taille supérieure aux autres boutons, fond en couleur d'accentuation
- Boutons secondaires (précédent/suivant/volume/plein écran) : icônes sans fond, légère mise en évidence au survol
- Barre de progression : fine, coins arrondis, portion lue en couleur d'accentuation, curseur visible au survol/drag uniquement
- Aucun changement de signal/slot dans `controls_widget.py`/`progress_widget.py` — uniquement des feuilles de style QSS et, si nécessaire, des ajustements de layout (tailles, marges)
- `pytest tests/test_ui_integration.py -v` affiche exactement les mêmes tests passants qu'en V1/V2, sans assertion modifiée

**Fichiers concernés :** `ui/controls_widget.py`, `ui/progress_widget.py`, feuilles de style QSS

**Dépendances :** US-140

**Notes pour Claude Code :** avant de modifier ces deux fichiers, lister les assertions actuelles de `tests/test_ui_integration.py` les concernant — ce sont les lignes qui ne doivent jamais changer, seul le rendu visuel évolue.

### US-151 — Restyler la grille de playlist

**En tant qu'**utilisateur, **je veux** une playlist visuellement plus dense et lisible, **afin de** identifier rapidement mes fichiers (F23 du PRD V3).

**Critères d'acceptation :**
- Vignettes à coins arrondis (cohérent avec US-150)
- Surbrillance ou changement de fond au survol d'un élément
- L'élément en cours de lecture reste visuellement distinct (V1 US-041), restylé pour cohérence avec la nouvelle palette
- Durée affichée en overlay discret dans le coin inférieur droit de la vignette, plutôt qu'en texte séparé sous le titre
- Aucun changement de comportement (sélection, double-clic, suppression) — uniquement le rendu visuel

**Fichiers concernés :** `ui/playlist_widget.py`, feuilles de style QSS

**Dépendances :** US-140

**Notes pour Claude Code :** réutiliser directement les miniatures déjà générées par `core/thumbnail_generator.py` (V2 F16) — aucune modification de la génération de miniatures elle-même dans cette story.

### US-152 — Restyler les paramètres

**En tant qu'**utilisateur, **je veux** une page de paramètres organisée et cohérente visuellement, **afin de** trouver facilement les réglages que je cherche (F24 du PRD V3).

**Critères d'acceptation :**
- Réglages regroupés en sections visuellement séparées (ex. Lecture, Apparence, À propos)
- Chaque ligne de réglage suit le pattern : icône à gauche, libellé + description courte en gris, contrôle aligné à droite
- Les options booléennes utilisent des toggles stylés plutôt que des cases à cocher
- Le dialogue reste modal (décision actée en PRD V3 section 9) — aucun changement de ce comportement
- Le sélecteur de couleur d'accentuation (US-141) est intégré dans la section Apparence selon ce nouveau pattern visuel

**Fichiers concernés :** composant de paramètres existant (V2 F15)

**Dépendances :** US-141

**Notes pour Claude Code :** c'est une réorganisation visuelle d'un composant existant, pas une recréation — vérifier qu'aucun réglage fonctionnel n'est perdu ou dupliqué en cours de restylage (thème, couleur d'accentuation, gestion V2 des dossiers si applicable).

### US-153 — Restyler le mini-mode et implémenter le comportement configurable du bouton fermer

**En tant qu'**utilisateur, **je veux** un mini-mode visuellement cohérent avec le reste de l'application et un bouton fermer dont le comportement correspond à mes attentes, **afin de** contrôler la lecture en arrière-plan sans surprise (F26 du PRD V3).

**Critères d'acceptation :**
- Fenêtre à coins arrondis, barre de titre minimaliste (icône + "Lecteur multimédia" + bouton fermer)
- Contrôles de lecture superposés au centre de la vidéo, réutilisant explicitement le composant overlay créé en US-130/US-131 (même style, même comportement de masquage à 5 secondes)
- Icône d'agrandissement en bas à droite, comportement fixe : retour à la fenêtre principale avec lecture conservée
- Bouton fermer (X) : par défaut, minimise l'application (dock/barre des tâches) ; si l'option "Fermer l'application" est activée dans les paramètres restylés (US-152), ferme l'application à la place
- Nouvelle clé `mini_mode_close_behavior` (`minimize` par défaut / `close`) ajoutée à `core/settings_manager.py` et exposée dans les paramètres (US-152)
- Un test `tests/test_settings_manager.py` (étendu) vérifie la lecture/écriture de cette nouvelle clé, sans modifier les assertions existantes sur les autres clés

**Fichiers concernés :** `ui/mini_mode_window.py`, `core/settings_manager.py` (deuxième exception `core/` actée en PRD V3 section 1), composant de paramètres (US-152)

**Dépendances :** US-130, US-131, US-100/US-101 (V2, mini-mode fonctionnel), US-152

**Notes pour Claude Code :** l'ajout de la clé `mini_mode_close_behavior` à `settings_manager.py` doit suivre exactement le même pattern que les clés existantes (thème, couleur d'accentuation) — pas de mécanisme de persistance parallèle ou différent pour cette seule clé.

---

## Phase 16 — Pochette audio

### US-160 — Exposer la métadonnée de pochette dans PlayerEngine

**En tant que** développeur, **je veux** que `PlayerEngine` expose l'image de pochette du média audio en cours, **afin de** permettre son affichage dans la zone vidéo (F27 du PRD V3).

**Critères d'acceptation :**
- `core/player_engine.py` gagne une méthode ou propriété (ex. `get_cover_art() -> QImage | None`) interrogeant `QMediaPlayer.metaData()` pour la clé `QMediaMetaData.Key.CoverArtImage`, avec repli sur `ThumbnailImage` si absente
- Retourne `None` si aucune des deux clés n'est présente (ex. fichier vidéo, ou fichier audio sans métadonnées embarquées) — pas d'exception levée
- Un test `tests/test_player_engine.py` (étendu) vérifie : fichier audio avec pochette embarquée retourne une image non vide, fichier audio sans pochette retourne `None`, fichier vidéo retourne `None` (la question ne se pose pas pour un contenu vidéo)
- **Critère de non-régression explicite :** cette méthode est purement additive — `git diff` sur `core/player_engine.py` ne doit modifier aucune méthode existante (`load`, `play`, `pause`, `stop`, `set_playback_rate`)

**Fichiers concernés :** `core/player_engine.py`, `tests/test_player_engine.py`

**Dépendances :** US-020 (V1)

**Notes pour Claude Code :** si aucun fichier de test avec pochette embarquée n'est disponible dans `tests/fixtures/`, documenter cette limite explicitement plutôt que de fabriquer un résultat de test non vérifié — cohérent avec la note déjà donnée en V1 US-020 sur les fixtures de test.

### US-161 — Afficher la pochette ou l'icône générique dans la zone vidéo

**En tant qu'**utilisateur, **je veux** voir la pochette de l'album (ou une icône générique) lors de l'écoute d'un fichier audio, **afin de** ne pas avoir un écran noir/vide pendant la lecture (F27 du PRD V3).

**Critères d'acceptation :**
- Au chargement d'un média, `ui/video_widget.py` interroge `PlayerEngine.get_cover_art()` (US-160) et bascule son affichage : `QVideoWidget` pour un contenu vidéo, image de pochette (ou icône générique) pour un contenu audio
- Si une pochette est disponible : affichée centrée, mise à l'échelle sans déformation (letterboxing si le ratio ne correspond pas)
- Si aucune pochette n'est disponible : icône générique (note de musique) teintée avec la couleur d'accentuation active (US-140), affichée centrée
- Ce comportement est identique et sans code dupliqué dans les trois contextes : fenêtre normale, plein écran (US-130), mini-mode (US-153) — puisque les trois réutilisent la même instance de `video_widget.py`
- La bascule entre pochette et vidéo lors du passage d'un fichier audio à un fichier vidéo dans la file de lecture ne produit aucun artefact visuel perceptible (flash, redimensionnement brusque)

**Fichiers concernés :** `ui/video_widget.py`

**Dépendances :** US-160, US-140 (couleur d'accentuation pour l'icône générique)

**Notes pour Claude Code :** tester explicitement ce comportement dans les trois contextes listés ci-dessus avant de considérer la story terminée — le risque principal n'est pas l'affichage lui-même mais un oubli de propagation si un des trois contextes s'avère, à l'usage, moins directement connecté à `video_widget.py` que prévu par l'architecture (auquel cas, s'arrêter et signaler l'écart plutôt que dupliquer la logique d'affichage).

---
---

# User Stories V3 (English) — Audio/Video Player, PyQt6 + QtMultimedia (Visual restyling)

**Companion document to** `PRD_V3_Lecteur_Media_PyQt6.md`
**Prerequisite:** V1 and V2 complete
**Usage:** sequential execution by Claude Code. Phase 14 (colours) must precede Phase 15 (restyling of components that consume the accent colour). Phase 13 (fullscreen) and Phase 16 (audio cover art) are independent of the rest and reorderable.

**ID convention:** `US-PPNN`, continuing the numeric sequence of the V1/V2 IDs.

**Non-negotiable reminder:** this V3 is a restyle. No existing V1/V2 test assertion is to be modified. Any story that appears to require a functional behaviour change (beyond the two `core/` exceptions made in the V3 PRD, section 1) must stop and flag the discrepancy rather than silently implementing it.

---

## Phase 13 — Fullscreen overlay

### US-130 — Create the overlay controls component

**As a** user, **I want** to see playback controls overlaid on the video in fullscreen rather than in a separate bar, **so that** I get an immersive experience (PRD V3 F21).

**Acceptance criteria:**
- On entering fullscreen (entry behaviour already defined in V2 US-082), `ui/controls_widget.py` is repositioned as a centred overlay on `ui/video_widget.py`, with a semi-transparent background, rather than duplicated into a new widget
- The buttons shown in the overlay are functionally identical to those in the normal bar (same signals, same ViewModel) — only positioning and QSS styling differ
- On exiting fullscreen, `controls_widget.py` returns to its normal position (docked at the bottom of the window) with no restart or state reset

**Files involved:** `ui/video_widget.py`, `ui/controls_widget.py`, QSS stylesheets for overlay mode

**Dependencies:** US-082 (V2, fullscreen entry/exit)

**Notes for Claude Code:** do not create a second controls widget for overlay mode — reuse the existing instance and change its parent/positioning depending on mode (normal vs. fullscreen). Explicitly verify that `tests/test_ui_integration.py` (V1/V2) still passes unmodified, since `controls_widget.py` changes its positioning behaviour but not its logic.

### US-131 — Implement auto-hide on inactivity

**As a** user, **I want** the overlay controls to disappear after a period of mouse inactivity, **so that** I can watch without visual distraction (PRD V3 F21).

**Acceptance criteria:**
- A 5-second `QTimer` resets on every `mouseMoveEvent` detected on the fullscreen window
- On timer expiry, the overlay controls disappear with a fade (`QPropertyAnimation` on a `QGraphicsOpacityEffect`, or a simple `hide()` fallback if the animation proves unstable — decision made in PRD V3 section 8)
- Any mouse movement after the controls disappear triggers an immediate fade-back-in and resets the timer
- If the mouse is directly hovering over the controls area, the timer is suspended until it leaves
- If playback is paused, the controls remain permanently visible, independent of the timer

**Files involved:** `ui/video_widget.py` (handling `mouseMoveEvent` and the timer), `ui/controls_widget.py` (visible/hidden state)

**Dependencies:** US-130

**Notes for Claude Code:** verify the pause behaviour explicitly first (the simplest case: timer disabled), before coding the hover-suspension logic, which is subtler (distinguishing "mouse still over the controls" from "mouse still elsewhere on the video").

---

## Phase 14 — Colour system

### US-140 — Extend the theme with an accent colour

**As a** developer, **I want** a centralised accent-colour mechanism, **so that** the components restyled in later phases can reference it consistently (PRD V3 F25).

**Acceptance criteria:**
- `ui/theme_manager.py` (V2) gains a notion of accent colour, chosen from a predefined palette (at least 4–5 colours, e.g. blue, purple, green, orange, red)
- The `dark.qss`/`light.qss` stylesheets use a dynamically injected accent-colour variable (via string substitution in the generated QSS, `QPalette`, or equivalent) rather than a hard-coded colour
- The accent-colour choice is persisted via `core/settings_manager.py` (V2), using a key distinct from the dark/light theme key
- A `tests/test_theme_manager.py` test (extended if it exists, otherwise created) verifies that changing the accent colour actually updates the value injected into the generated stylesheet

**Files involved:** `ui/theme_manager.py`, `ui/resources/dark.qss`, `ui/resources/light.qss`

**Dependencies:** US-083 (V2, dark/light theme)

**Notes for Claude Code:** do not wire up a UI control for choosing the colour in this story yet — it only prepares the mechanism. The user-facing control is added in US-141.

### US-141 — Add the accent-colour picker to settings

**As a** user, **I want** to choose my accent colour from the settings, **so that** I can personalise the application's appearance.

**Acceptance criteria:**
- The existing settings component (V2 F15) gains a control (e.g. a row of clickable colour swatches) allowing selection from the palette defined in US-140
- The selection applies immediately to the interface, with no application restart
- The choice persists across restarts (via `settings_manager.py`, US-140)

**Files involved:** the existing settings component (V2 F15)

**Dependencies:** US-140

**Notes for Claude Code:** this story may appear to overlap with F24 (Phase 15, the full settings restyle) — that is intentional: US-141 adds the minimal functionality to the existing component as-is, and US-152 (Phase 15) will later restyle the whole settings component around this functionality, not the other way round.

---

## Phase 15 — Component restyling

### US-150 — Restyle the playback bar

**As a** user, **I want** a visually polished playback bar consistent with my chosen accent colour, **so that** I enjoy a more pleasant interface (PRD V3 F22).

**Acceptance criteria:**
- Play/pause button: circular, larger than the other buttons, filled with the accent colour
- Secondary buttons (previous/next/volume/fullscreen): icons with no background, a subtle highlight on hover
- Progress bar: thin, rounded corners, the played portion shown in the accent colour, a handle visible only on hover/drag
- No change to any signal/slot in `controls_widget.py`/`progress_widget.py` — only QSS stylesheets and, if needed, layout adjustments (sizes, margins)
- `pytest tests/test_ui_integration.py -v` shows exactly the same passing tests as in V1/V2, with no assertion modified

**Files involved:** `ui/controls_widget.py`, `ui/progress_widget.py`, QSS stylesheets

**Dependencies:** US-140

**Notes for Claude Code:** before modifying these two files, list the current assertions in `tests/test_ui_integration.py` concerning them — these are the lines that must never change; only the visual rendering evolves.

### US-151 — Restyle the playlist grid

**As a** user, **I want** a visually denser and more readable playlist, **so that** I can quickly identify my files (PRD V3 F23).

**Acceptance criteria:**
- Rounded-corner thumbnails (consistent with US-150)
- A highlight or background change on hover
- The currently playing item remains visually distinct (V1 US-041), restyled for consistency with the new palette
- Duration shown as a discreet overlay in the thumbnail's bottom-right corner, rather than as separate text under the title
- No behavioural change (selection, double-click, deletion) — only visual rendering

**Files involved:** `ui/playlist_widget.py`, QSS stylesheets

**Dependencies:** US-140

**Notes for Claude Code:** reuse the thumbnails already generated by `core/thumbnail_generator.py` (V2 F16) directly — no change to thumbnail generation itself in this story.

### US-152 — Restyle settings

**As a** user, **I want** an organised, visually consistent settings screen, **so that** I can easily find the settings I am looking for (PRD V3 F24).

**Acceptance criteria:**
- Settings grouped into visually separated sections (e.g. Playback, Appearance, About)
- Each settings row follows the pattern: icon on the left, label + short grey description, a right-aligned control
- Boolean options use styled toggles rather than checkboxes
- The dialog remains modal (decision made in PRD V3 section 9) — no change to this behaviour
- The accent-colour picker (US-141) is integrated into the Appearance section following this new visual pattern

**Files involved:** the existing settings component (V2 F15)

**Dependencies:** US-141

**Notes for Claude Code:** this is a visual reorganisation of an existing component, not a rebuild from scratch — verify that no functional setting is lost or duplicated during restyling (theme, accent colour, V2 folder management if applicable).

### US-153 — Restyle mini-mode and implement the configurable close-button behaviour

**As a** user, **I want** a mini-mode visually consistent with the rest of the application, and a close button whose behaviour matches my expectations, **so that** I can control background playback without surprises (PRD V3 F26).

**Acceptance criteria:**
- A rounded-corner window, a minimalist title bar (icon + "Media Player" + close button)
- Playback controls overlaid at the centre of the video, explicitly reusing the overlay component created in US-130/US-131 (same style, same 5-second auto-hide behaviour)
- An expand icon at the bottom right, with fixed behaviour: returns to the main window with playback preserved
- Close button (X): by default, minimises the application (dock/taskbar); if the "Close the application" option is enabled in the restyled settings (US-152), it closes the application instead
- A new `mini_mode_close_behavior` key (`minimize` default / `close`) is added to `core/settings_manager.py` and exposed in settings (US-152)
- A `tests/test_settings_manager.py` test (extended) verifies reading/writing this new key, without modifying existing assertions for other keys

**Files involved:** `ui/mini_mode_window.py`, `core/settings_manager.py` (the second `core/` exception made in PRD V3 section 1), the settings component (US-152)

**Dependencies:** US-130, US-131, US-100/US-101 (V2, functional mini-mode), US-152

**Notes for Claude Code:** adding the `mini_mode_close_behavior` key to `settings_manager.py` must follow exactly the same pattern as existing keys (theme, accent colour) — no parallel or different persistence mechanism for this single key.

---

## Phase 16 — Audio cover art

### US-160 — Expose cover-art metadata in PlayerEngine

**As a** developer, **I want** `PlayerEngine` to expose the cover-art image of the currently playing audio media, **so that** it can be displayed in the video area (PRD V3 F27).

**Acceptance criteria:**
- `core/player_engine.py` gains a method or property (e.g. `get_cover_art() -> QImage | None`) querying `QMediaPlayer.metaData()` for the `QMediaMetaData.Key.CoverArtImage` key, falling back to `ThumbnailImage` if absent
- Returns `None` if neither key is present (e.g. a video file, or an audio file with no embedded metadata) — no exception raised
- A `tests/test_player_engine.py` test (extended) verifies: an audio file with embedded cover art returns a non-empty image, an audio file with no cover art returns `None`, a video file returns `None` (the question does not arise for video content)
- **Explicit non-regression criterion:** this method is purely additive — `git diff` on `core/player_engine.py` must not modify any existing method (`load`, `play`, `pause`, `stop`, `set_playback_rate`)

**Files involved:** `core/player_engine.py`, `tests/test_player_engine.py`

**Dependencies:** US-020 (V1)

**Notes for Claude Code:** if no test file with embedded cover art is available in `tests/fixtures/`, explicitly document this limitation rather than fabricating an unverified test result — consistent with the note already given in V1 US-020 about test fixtures.

### US-161 — Display cover art or the generic icon in the video area

**As a** user, **I want** to see the album cover (or a generic icon) while listening to an audio file, **so that** I do not see a black/empty screen during playback (PRD V3 F27).

**Acceptance criteria:**
- On loading a media item, `ui/video_widget.py` queries `PlayerEngine.get_cover_art()` (US-160) and toggles its display: `QVideoWidget` for video content, cover-art image (or generic icon) for audio content
- If cover art is available: displayed centred, scaled without distortion (letterboxing if the aspect ratio does not match)
- If no cover art is available: a generic icon (a musical note), tinted with the active accent colour (US-140), displayed centred
- This behaviour is identical, with no duplicated code, across all three contexts: the normal window, fullscreen (US-130), and mini-mode (US-153) — since all three reuse the same `video_widget.py` instance
- Switching between cover art and video when moving from an audio file to a video file in the play queue produces no perceptible visual artefact (flash, abrupt resizing)

**Files involved:** `ui/video_widget.py`

**Dependencies:** US-160, US-140 (accent colour for the generic icon)

**Notes for Claude Code:** explicitly test this behaviour in all three contexts listed above before considering the story complete — the main risk is not the display itself but a propagation gap if one of the three contexts turns out, in practice, to be less directly connected to `video_widget.py` than the architecture assumes (in which case, stop and flag the discrepancy rather than duplicating the display logic).
