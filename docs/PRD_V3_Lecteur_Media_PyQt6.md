# PRD V3 — Lecteur Audio/Vidéo PyQt6 + QtMultimedia (Restylage visuel)

**Document compagnon de** `PRD_Lecteur_Media_PyQt6.md` (V1), `PRD_V2_Lecteur_Media_PyQt6.md` (V2)
**Statut :** Draft V2 (recadré après retour utilisateur — un premier brouillon de ce document proposait une refonte d'architecture, hors sujet)
**Date :** Juillet 2026
**Prérequis :** V1 et V2 complètes
**Référence visuelle :** captures d'écran de l'app Windows 11 "Lecteur multimédia"

---

## 1. Contexte et objectif

Cette V3 est un **restylage visuel pur**. La fenêtre unique actuelle (vidéo + contrôles + playlist) est conservée telle quelle dans sa structure ; aucun fichier `core/` n'est modifié ; aucune nouvelle page ni navigation multi-écrans n'est introduite. L'objectif est de rendre l'interface existante plus soignée, cohérente et agréable à l'usage, en s'inspirant de l'esthétique des captures Windows Media Player, sans en reprendre l'organisation en pages/bibliothèque.

**Périmètre de cette V3 :**
1. Un mode plein écran avec contrôles superposés à masquage automatique (fonctionnalité concrète, précisée en section 3)
2. Un restylage visuel de tous les composants existants (barre de lecture, grille de playlist, paramètres) selon un système de couleurs et de style cohérent

**Hors scope explicite (rejeté après clarification) :**
- Séparation Bibliothèque / File d'attente / Playlists
- Scan de dossiers, indexation, historique de médias récents
- Sidebar de navigation ou toute nouvelle page
- Lecture de métadonnées audio avancées (tags ID3 complets, artiste/album/genre) — seule l'image de pochette (F27) est concernée, via l'API native `QMediaMetaData` de Qt, pas un parsing ID3 manuel

**Exceptions actées à la règle "aucun fichier `core/` modifié" :**
- `core/player_engine.py` reçoit un ajout minimal pour exposer la métadonnée de pochette déjà fournie par `QMediaPlayer` (F27)
- `core/settings_manager.py` (existant depuis V2 F15) reçoit une nouvelle clé de préférence pour le comportement du bouton fermer en mini-mode (F26) — réutilisation du mécanisme de persistance déjà en place, pas de nouveau fichier

Ce sont les deux seules touches à `core/` de cette V3 — tout le reste reste strictement du restylage `ui/`.

---

## 2. Référence visuelle (ce qu'on en retient pour le style, appliqué à l'existant)

- **Palette :** thème sombre par défaut, une couleur d'accentuation appliquée aux éléments actifs (bouton play, slider de progression, élément survolé)
- **Barre de lecture :** bouton play/pause circulaire proéminent au centre, icônes secondaires (volume, plein écran, sous-titres) sobres et alignées à droite, ligne de progression fine et cliquable
- **Grille de playlist :** vignettes à coins arrondis, légère ombre ou surbrillance au survol, titre et durée lisibles sous chaque élément
- **Paramètres :** présentation en sections groupées, chaque ligne = icône + libellé + description courte en gris + contrôle aligné à droite (toggle plutôt que case à cocher)

Ces éléments sont appliqués à la structure actuelle de l'application (une fenêtre, un panneau playlist, une barre de contrôles, un dialogue paramètres) — ils ne créent aucune nouvelle organisation d'écrans.

---

## 3. Fonctionnalités détaillées

### F21 — Plein écran avec contrôles superposés à masquage automatique

**Description :** en mode plein écran, la vidéo occupe tout l'écran ; les contrôles de lecture s'affichent en superposition (overlay semi-transparent) par-dessus la vidéo, et se masquent automatiquement après une période d'inactivité de la souris.

**Comportement précis :**
- Entrée en plein écran (double-clic sur la vidéo ou raccourci, comportement déjà défini en V2 US-082) : les contrôles overlay apparaissent immédiatement
- Après 5 secondes sans mouvement de souris : fondu de sortie des contrôles, la vidéo reste seule à l'écran
- Tout mouvement de souris : fondu d'entrée immédiat des contrôles, réinitialisation du minuteur d'inactivité
- Si la souris survole directement les contrôles (ex. pour ajuster le volume), ils restent affichés tant qu'elle ne les quitte pas, indépendamment du minuteur
- Si la lecture est en pause, les contrôles restent visibles en permanence (masquer les contrôles pendant une pause n'aurait pas de sens pour l'utilisateur)
- Sortie du plein écran (Échap) : retour à la barre de lecture standard, toujours visible

**Composants concernés :** `ui/video_widget.py` (accueille l'overlay), `ui/controls_widget.py` (réutilisé en mode superposition plutôt que dupliqué — un seul jeu de contrôles, positionné différemment selon le mode plein écran ou non)

**Point d'attention technique :** le minuteur d'inactivité (`QTimer`) se réinitialise sur `mouseMoveEvent` de la fenêtre en plein écran. Le fondu (opacity animée via `QPropertyAnimation` sur un `QGraphicsOpacityEffect`, ou simple `show()`/`hide()` si l'animation s'avère complexe à intégrer proprement) doit rester fluide, sans à-coup visuel perceptible.

### F22 — Refonte visuelle de la barre de lecture

**Description :** restylage de `ui/controls_widget.py` et `ui/progress_widget.py` existants, sans changement de leur logique ni de leur API vis-à-vis du ViewModel.

**Détails de style :**
- Bouton play/pause : forme circulaire, taille plus importante que les autres boutons, couleur d'accentuation en fond
- Boutons secondaires (précédent/suivant, volume, plein écran) : icônes simples, sans fond, légère mise en évidence au survol
- Barre de progression : fine, coins arrondis, curseur visible uniquement au survol ou pendant le drag, couleur d'accentuation pour la portion déjà lue

**Composants concernés :** `ui/controls_widget.py`, `ui/progress_widget.py` (feuilles de style QSS uniquement, aucun changement de signaux/slots)

### F23 — Refonte visuelle de la grille de playlist

**Description :** restylage de `ui/playlist_widget.py`, réutilisant les miniatures déjà générées en V2 (F16).

**Détails de style :**
- Vignettes à coins arrondis (cohérent avec F22)
- Légère surbrillance ou changement de fond au survol d'un élément
- L'élément en cours de lecture reste visuellement distinct (déjà existant en V1 US-041, restylé pour cohérence avec la nouvelle palette)
- Durée affichée en overlay discret sur la vignette (coin inférieur droit), plutôt qu'en texte séparé, pour un rendu plus dense et cohérent avec la capture 3

**Composants concernés :** `ui/playlist_widget.py`

### F24 — Refonte visuelle des paramètres

**Description :** restylage du dialogue de paramètres existant (thème V2 F15), organisé en sections groupées avec un pattern visuel cohérent, sans le transformer en page de navigation séparée — reste un dialogue ou panneau accessible depuis l'application actuelle.

**Détails de style :**
- Sections groupées par thématique (ex. Lecture, Apparence, À propos), séparées visuellement
- Chaque ligne de réglage : icône à gauche, libellé + description courte, contrôle aligné à droite
- Toggles stylés (switch) pour les options booléennes plutôt que des cases à cocher

**Composants concernés :** composant de paramètres existant (créé en V2 F15, fichier exact à identifier selon l'implémentation réelle de cette story)

**Précision sur la décision actée (section 9) :** modal signifie que l'utilisateur ne peut pas interagir avec le reste de l'application tant que la boîte de dialogue est ouverte (pas de clic sur play/pause, pas de navigation dans la playlist) — mais la lecture en cours n'est pas mise en pause automatiquement à l'ouverture, sauf si tu préfères ce comportement également (à préciser si besoin lors de l'implémentation).

### F25 — Système de couleurs et couleur d'accentuation

**Description :** formalise et étend le thème sombre/clair de V2 (F15) avec une couleur d'accentuation configurable, utilisée de façon cohérente par F21 à F24.

**Détails :**
- Palette de couleurs d'accentuation prédéfinies (choix limité, pas de sélecteur RGB libre)
- Appliquée aux éléments interactifs actifs : bouton play, portion lue de la barre de progression, élément de playlist en cours, bordures de focus
- Contrôle ajouté dans les paramètres restylés (F24)

**Composants concernés :** `ui/theme_manager.py` (V2), feuilles de style QSS existantes (`dark.qss`, `light.qss`) étendues avec des variables de couleur d'accentuation

### F26 — Design du mini-mode

**Description :** restylage visuel de `ui/mini_mode_window.py` (créé fonctionnellement en V2 US-100/US-101), en réutilisant le composant de contrôles superposés défini en F21 plutôt que d'en créer un nouveau.

**Détails de style (d'après la capture de référence) :**
- Fenêtre compacte à coins arrondis, fond sombre cohérent avec le thème actif
- Barre de titre minimaliste : icône de l'application, titre "Lecteur multimédia", bouton de fermeture (X) — pas de bouton minimiser/agrandir natif puisque la fenêtre est déjà réduite
- Contrôles de lecture (précédent / play-pause / suivant) superposés au centre de la vidéo, réutilisant exactement le style et le composant overlay de F21 (bouton play/pause circulaire avec anneau de couleur d'accentuation, boutons secondaires sobres)
- Icône d'agrandissement en bas à droite, pour revenir à la fenêtre principale
- Barre de progression fine sur toute la largeur, en bas de la fenêtre, cohérente avec le style défini en F22

**Hypothèse à confirmer :** ~~le bouton de fermeture (X) et l'icône d'agrandissement correspondent à deux actions distinctes~~ **Décision actée :** le bouton fermer (X) **minimise l'application par défaut** (comportement équivalent à l'icône d'agrandissement du point de vue de la lecture, qui continue en arrière-plan), avec une option dans les Paramètres restylés (F24) permettant de basculer ce comportement vers "Fermer l'application" à la place. L'icône d'agrandissement, elle, revient toujours explicitement à la fenêtre principale (comportement fixe, non paramétrable).

**Comportement des contrôles superposés :** confirmé — réutilisation du même comportement de masquage automatique que F21 (apparition au survol/mouvement de souris, masquage après 5 secondes d'inactivité), pour une cohérence totale avec le plein écran.

**Composants concernés :** `ui/mini_mode_window.py` (restylage, réutilisation du composant overlay F21) ; nouvelle option dans `ui/pages/settings_page.py`-équivalent (F24) pour le comportement du bouton fermer, persistée via `core/settings_manager.py` (clé `mini_mode_close_behavior`, valeurs `minimize` [défaut] / `close`)

### F27 — Affichage de la pochette pour les fichiers audio

**Description :** pour un fichier audio (sans piste vidéo), la zone normalement occupée par la vidéo affiche la pochette embarquée dans le fichier plutôt qu'un écran noir/vide. Comportement identique en fenêtre normale, plein écran et mini-mode.

**Comportement précis :**
- Au chargement d'un fichier audio, `PlayerEngine` interroge `QMediaPlayer.metaData()` pour récupérer l'image de pochette (clé `QMediaMetaData.Key.CoverArtImage`, ou `ThumbnailImage` en repli si `CoverArtImage` est absente)
- Si une image est trouvée : elle s'affiche centrée dans la zone vidéo, mise à l'échelle pour remplir au mieux l'espace disponible sans déformation (letterboxing si le ratio de la pochette ne correspond pas au ratio de la zone d'affichage)
- Si aucune image n'est trouvée : une icône générique (note de musique) s'affiche à la place, **teintée avec la couleur d'accentuation active (F25)** plutôt qu'une couleur statique — cohérente automatiquement quel que soit le choix de couleur de l'utilisateur
- Au passage d'un fichier audio à un fichier vidéo (ou l'inverse) dans la file de lecture, la bascule entre affichage pochette et affichage vidéo se fait sans artefact visuel perceptible

**Composants concernés :**
- `core/player_engine.py` — ajout minimal exposant la métadonnée de pochette du média courant (seule modification `core/` de cette V3, cf. section 1)
- `ui/video_widget.py` — bascule entre `QVideoWidget` (contenu vidéo) et affichage de pochette (`QLabel`/`QPixmap` ou équivalent) selon la présence d'une piste vidéo

**Point d'attention technique :** cette bascule d'affichage doit se faire au niveau du widget vidéo lui-même, pas être dupliquée dans `MainWindow`, `MiniModeWindow` et le mode plein écran séparément — les trois contextes partagent déjà le même `video_widget.py` (architecture validée par F21/F26), donc F27 en hérite naturellement sans travail supplémentaire par contexte.

---

## 4. Composants UI concernés (vue d'ensemble)

Aucun nouveau fichier `core/` — une seule exception ponctuelle sur un fichier existant (F27, justifiée en section 1). Fichiers `ui/` modifiés (restylage uniquement, API/signaux inchangés sauf mention contraire) :

```
media_player/
├── core/
│   ├── player_engine.py    # MODIFIÉ — exposition de la métadonnée pochette (F27), exception core/
│   └── settings_manager.py # MODIFIÉ — nouvelle clé mini_mode_close_behavior (F26), exception core/
└── ui/
    ├── video_widget.py       # MODIFIÉ — accueille l'overlay plein écran (F21) et l'affichage pochette (F27)
    ├── controls_widget.py    # MODIFIÉ — restylage + réutilisé en overlay (F21, F22)
    ├── progress_widget.py    # MODIFIÉ — restylage (F22)
    ├── playlist_widget.py    # MODIFIÉ — restylage (F23)
    ├── mini_mode_window.py   # MODIFIÉ — restylage, réutilise l'overlay F21 (F26)
    ├── theme_manager.py      # MODIFIÉ — couleur d'accentuation (F25)
    └── resources/
        ├── dark.qss           # MODIFIÉ — variables de couleur d'accentuation
        └── light.qss          # MODIFIÉ — variables de couleur d'accentuation
```

---

## 5. Exigences non fonctionnelles

| Catégorie | Exigence |
|---|---|
| Non-régression | Aucun test V1/V2 existant ne doit être modifié dans ses assertions — ce sont des changements de style (QSS, layout), pas de comportement |
| Performance | Le fondu d'apparition/disparition des contrôles en plein écran ne doit introduire aucune latence perceptible sur la lecture vidéo elle-même |
| Cohérence visuelle | Une seule feuille de style de référence par thème (dark/light), pas de couleur codée en dur dans un widget individuel |
| Accessibilité | Les raccourcis clavier existants (V1 F11) restent fonctionnels en plein écran, y compris quand les contrôles sont masqués |

---

## 6. Plan de développement

| Phase | Contenu | Sortie attendue |
|---|---|---|
| Phase 13 — Plein écran overlay | F21 | Contrôles superposés fonctionnels, masquage/réapparition fluide |
| Phase 14 — Système de couleurs | F25 | Couleur d'accentuation configurable, appliquée aux feuilles de style existantes |
| Phase 15 — Restylage des composants | F22, F23, F24, F26 | Barre de lecture, playlist, paramètres et mini-mode restylés selon le système F25 |
| Phase 16 — Pochette audio | F27 | Affichage de pochette pour les fichiers audio, cohérent sur les trois contextes (normal, plein écran, mini-mode) |

**Remarque :** F25 doit précéder F22/F23/F24, puisque ces dernières consomment la couleur d'accentuation définie par F25. F21 (plein écran) est indépendante et peut être développée en parallèle ou avant.

---

## 7. Critères d'acceptation (V3 Definition of Done)

1. Le plein écran affiche des contrôles en superposition qui se masquent après 5 secondes d'inactivité de la souris et réapparaissent au moindre mouvement
2. Les contrôles restent visibles en permanence en plein écran si la lecture est en pause ou si la souris est sur les contrôles
3. La barre de lecture, la grille de playlist et les paramètres suivent un système de couleurs cohérent, avec une couleur d'accentuation configurable
4. Le mini-mode réutilise visuellement les mêmes contrôles superposés que le plein écran (F21), sans duplication de composant
5. Les fichiers audio affichent leur pochette embarquée (ou une icône générique à défaut) dans la zone vidéo, de façon identique en fenêtre normale, plein écran et mini-mode
6. Aucun changement de comportement fonctionnel n'est observable par rapport à la V2 en dehors de F27 — uniquement l'apparence change
7. 100% des tests V1/V2 existants passent sans modification de leurs assertions

---

## 8. Risques identifiés

| Risque | Impact | Mitigation |
|---|---|---|
| Réutiliser `controls_widget.py` à la fois en mode normal et en overlay plein écran peut introduire de la complexité de positionnement | Moyen | Séparer clairement le style (QSS conditionnel selon le mode) de la logique (widget identique, signaux inchangés) |
| Animation de fondu mal maîtrisée avec `QPropertyAnimation`/`QGraphicsOpacityEffect` sur macOS | Faible | Prévoir un repli simple (`show()`/`hide()` sans animation) si l'animation s'avère instable, plutôt que de s'acharner |

---

## 9. Décisions actées

1. **Délai d'inactivité en plein écran :** 5 secondes.
2. **Comportement du dialogue Paramètres restylé (F24) :** reste modal, bloque l'interaction avec le reste de l'application le temps qu'il est ouvert — comportement inchangé par rapport à V2, seul le style change.
3. **Bouton fermer du mini-mode (F26) :** minimise l'application par défaut ; paramétrable dans les Paramètres restylés (F24) pour basculer vers "Fermer l'application" à la place.
4. **Masquage des contrôles en mini-mode (F26) :** identique au plein écran — 5 secondes d'inactivité.
5. **Icône de repli pour l'absence de pochette audio (F27) :** teintée avec la couleur d'accentuation active (F25), pas une couleur statique.

Toutes les questions ouvertes de ce PRD sont désormais tranchées — prêt pour la rédaction des user stories V3.

---
---

# PRD V3 (English) — Audio/Video Player, PyQt6 + QtMultimedia (Visual restyling)

**Companion document to** `PRD_Lecteur_Media_PyQt6.md` (V1), `PRD_V2_Lecteur_Media_PyQt6.md` (V2)
**Status:** Draft V2 (rescoped after user feedback — an earlier draft of this document proposed an architectural overhaul, which was out of scope)
**Date:** July 2026
**Prerequisite:** V1 and V2 complete
**Visual reference:** screenshots of the Windows 11 "Media Player" app

---

## 1. Background and objective

This V3 is a **pure visual restyling**. The current single window (video + controls + playlist) keeps its existing structure; no `core/` file is modified; no new page or multi-screen navigation is introduced. The goal is to make the existing interface more polished, consistent, and pleasant to use, drawing on the aesthetic of the Windows Media Player screenshots, without adopting its page/library organisation.

**Scope of this V3:**
1. A fullscreen mode with overlay controls that auto-hide (a concrete feature, detailed in section 3)
2. A visual restyling of all existing components (playback bar, playlist grid, settings) following a consistent colour and style system

**Explicitly out of scope (rejected after clarification):**
- Separating Library / Play Queue / Playlists
- Folder scanning, indexing, recent-media history
- A navigation sidebar or any new page
- Reading rich audio metadata (full ID3 tags, artist/album/genre) — only cover art (F27) is involved, via Qt's native `QMediaMetaData` API, not manual ID3 parsing

**Exceptions made to the "no `core/` file modified" rule:**
- `core/player_engine.py` receives a minimal addition to expose the cover-art metadata already provided by `QMediaPlayer` (F27)
- `core/settings_manager.py` (existing since V2 F15) receives a new preference key for the mini-mode close-button behaviour (F26) — reusing the already-established persistence mechanism, not a new file

These are the only two `core/` touches in this V3 — everything else remains strictly `ui/` restyling.

---

## 2. Visual reference (what is being taken for styling, applied to the existing app)

- **Palette:** a dark theme by default, an accent colour applied to active elements (the play button, the progress slider, the hovered item)
- **Playback bar:** a prominent circular play/pause button at the centre, understated secondary icons (volume, fullscreen, subtitles) aligned to the right, a thin, clickable progress line
- **Playlist grid:** rounded-corner thumbnails, a subtle shadow or highlight on hover, readable title and duration under each item
- **Settings:** presented in grouped sections, each row being icon + label + a short grey description + a right-aligned control (a toggle rather than a checkbox)

These elements are applied to the application's current structure (one window, one playlist panel, one control bar, one settings dialog) — they do not create any new screen organisation.

---

## 3. Feature detail

### F21 — Fullscreen with auto-hiding overlay controls

**Description:** in fullscreen mode, the video fills the entire screen; playback controls are displayed as a semi-transparent overlay on top of the video, and hide automatically after a period of mouse inactivity.

**Precise behaviour:**
- Entering fullscreen (double-click on the video, or the shortcut already defined in V2 US-082): the overlay controls appear immediately
- After 5 seconds of no mouse movement: the controls fade out, leaving the video alone on screen
- Any mouse movement: the controls immediately fade back in, resetting the inactivity timer
- If the mouse is directly hovering over the controls (e.g. to adjust volume), they remain visible for as long as it stays there, independent of the timer
- If playback is paused, the controls remain permanently visible (hiding controls during a pause would not make sense to the user)
- Exiting fullscreen (Escape): returns to the standard, always-visible playback bar

**Components involved:** `ui/video_widget.py` (hosts the overlay), `ui/controls_widget.py` (reused in overlay mode rather than duplicated — a single set of controls, positioned differently depending on fullscreen vs. normal mode)

**Technical point of attention:** the inactivity timer (`QTimer`) resets on the fullscreen window's `mouseMoveEvent`. The fade (animated opacity via `QPropertyAnimation` on a `QGraphicsOpacityEffect`, or a simple `show()`/`hide()` if the animation proves difficult to integrate cleanly) must remain smooth, with no perceptible visual stutter.

This is worth flagging as slightly more delicate than it looks: reusing the same `controls_widget.py` instance in two different positioning contexts (docked in the normal window vs. floating over the video in fullscreen) is a reasonable way to avoid duplicating logic, but it does mean the widget's parent and geometry change at runtime, which is a more fragile Qt pattern than it first appears. If it turns out to be more trouble than it is worth, a second, thin overlay widget that simply relays clicks to the same ViewModel is a perfectly acceptable fallback — the point made in section 8's risk table.

### F22 — Visual redesign of the playback bar

**Description:** restyling of the existing `ui/controls_widget.py` and `ui/progress_widget.py`, with no change to their logic or their API towards the ViewModel.

**Style detail:**
- Play/pause button: circular, larger than the other buttons, filled with the accent colour
- Secondary buttons (previous/next, volume, fullscreen): simple icons, no background, a subtle highlight on hover
- Progress bar: thin, rounded corners, a handle visible only on hover or while dragging, the already-played portion shown in the accent colour

**Components involved:** `ui/controls_widget.py`, `ui/progress_widget.py` (QSS stylesheets only, no change to signals/slots)

### F23 — Visual redesign of the playlist grid

**Description:** restyling of `ui/playlist_widget.py`, reusing the thumbnails already generated in V2 (F16).

**Style detail:**
- Rounded-corner thumbnails (consistent with F22)
- A subtle highlight or background change on hover
- The currently playing item remains visually distinct (already present since V1 US-041, restyled for consistency with the new palette)
- Duration shown as a discreet overlay on the thumbnail (bottom-right corner) rather than as separate text, for a denser look consistent with screenshot 3

**Components involved:** `ui/playlist_widget.py`

### F24 — Visual redesign of settings

**Description:** restyling of the existing settings dialog (V2 F15's theme), organised into grouped sections with a consistent visual pattern, without turning it into a separate navigation page — it remains a dialog or panel accessible from the current application.

**Style detail:**
- Sections grouped by theme (e.g. Playback, Appearance, About), visually separated
- Each settings row: icon on the left, label + short description, a right-aligned control
- Styled toggles (switches) for boolean options rather than checkboxes

**Components involved:** the existing settings component (created in V2 F15, exact file to be identified based on that story's actual implementation)

**Note on the decision made (section 9):** modal means the user cannot interact with the rest of the application while the dialog is open (no clicking play/pause, no navigating the playlist) — but current playback is not automatically paused when it opens, unless you would also prefer that behaviour (to be clarified during implementation if needed).

### F25 — Colour system and accent colour

**Description:** formalises and extends V2's dark/light theme (F15) with a configurable accent colour, used consistently by F21 through F24.

**Detail:**
- A predefined palette of accent colour choices (a limited set, no free RGB picker)
- Applied to active interactive elements: the play button, the played portion of the progress bar, the currently playing playlist item, focus outlines
- A control added to the restyled settings (F24)

**Components involved:** `ui/theme_manager.py` (V2), existing QSS stylesheets (`dark.qss`, `light.qss`) extended with accent-colour variables

### F26 — Mini-mode design

**Description:** visual restyling of `ui/mini_mode_window.py` (functionally built in V2 US-100/US-101), reusing the overlay controls component defined in F21 rather than creating a new one.

**Style detail (based on the reference screenshot):**
- A compact, rounded-corner window, dark background consistent with the active theme
- A minimalist title bar: application icon, "Media Player" title, close button (X) — no native minimise/maximise button, since the window is already reduced
- Playback controls (previous / play-pause / next) overlaid at the centre of the video, reusing exactly the style and overlay component from F21 (a circular play/pause button with an accent-coloured ring, understated secondary buttons)
- An expand icon at the bottom right, to return to the main window
- A thin progress bar spanning the full width at the bottom of the window, consistent with the style defined in F22

**Decision made:** the close button (X) **minimises the application by default** (equivalent in playback terms to the expand icon, with playback continuing in the background), with an option in the restyled Settings (F24) allowing this to be switched to "Close the application" instead. The expand icon always explicitly returns to the main window (fixed behaviour, not configurable).

**Overlay controls behaviour:** confirmed — reusing the same auto-hide behaviour as F21 (appearing on hover/mouse movement, hiding after 5 seconds of inactivity), for full consistency with fullscreen.

**Components involved:** `ui/mini_mode_window.py` (restyling, reusing the F21 overlay component); a new option in the `ui/pages/settings_page.py`-equivalent (F24) for the close-button behaviour, persisted via `core/settings_manager.py` (key `mini_mode_close_behavior`, values `minimize` [default] / `close`)

### F27 — Displaying cover art for audio files

**Description:** for an audio file (no video track), the area normally occupied by the video displays the file's embedded cover art rather than a black/empty screen. Behaviour is identical in the normal window, fullscreen, and mini-mode.

**Precise behaviour:**
- On loading an audio file, `PlayerEngine` queries `QMediaPlayer.metaData()` to retrieve the cover art image (the `QMediaMetaData.Key.CoverArtImage` key, falling back to `ThumbnailImage` if `CoverArtImage` is absent)
- If an image is found: it is displayed centred in the video area, scaled to best fill the available space without distortion (letterboxing if the cover's aspect ratio does not match the display area's)
- If no image is found: a generic icon (a musical note) is displayed instead, **tinted with the active accent colour (F25)** rather than a static colour — automatically consistent regardless of the user's colour choice
- When switching from an audio file to a video file (or vice versa) in the play queue, the transition between cover-art display and video display happens with no perceptible visual glitch

**Components involved:**
- `core/player_engine.py` — a minimal addition exposing the current media's cover-art metadata (the only `core/` change in this V3, see section 1)
- `ui/video_widget.py` — toggles between `QVideoWidget` (video content) and cover-art display (`QLabel`/`QPixmap` or equivalent) depending on whether a video track is present

**Technical point of attention:** this display toggle must happen at the level of the video widget itself, not be duplicated separately across `MainWindow`, `MiniModeWindow`, and fullscreen mode — all three contexts already share the same `video_widget.py` (an architecture validated by F21/F26), so F27 inherits this naturally with no extra per-context work.

---

## 4. UI components involved (overview)

No new `core/` file — a single one-off exception to an existing file (F27, justified in section 1). `ui/` files modified (restyling only, API/signals unchanged unless stated otherwise):

```
media_player/
├── core/
│   ├── player_engine.py    # MODIFIED — exposes cover-art metadata (F27), core/ exception
│   └── settings_manager.py # MODIFIED — new mini_mode_close_behavior key (F26), core/ exception
└── ui/
    ├── video_widget.py       # MODIFIED — hosts the fullscreen overlay (F21) and cover-art display (F27)
    ├── controls_widget.py    # MODIFIED — restyled + reused as overlay (F21, F22)
    ├── progress_widget.py    # MODIFIED — restyled (F22)
    ├── playlist_widget.py    # MODIFIED — restyled (F23)
    ├── mini_mode_window.py   # MODIFIED — restyled, reuses the F21 overlay (F26)
    ├── theme_manager.py      # MODIFIED — accent colour (F25)
    └── resources/
        ├── dark.qss           # MODIFIED — accent colour variables
        └── light.qss          # MODIFIED — accent colour variables
```

---

## 5. Non-functional requirements

| Category | Requirement |
|---|---|
| Non-regression | No existing V1/V2 test assertion is to be modified — these are style changes (QSS, layout), not behaviour changes |
| Performance | The controls' fade in/out in fullscreen must introduce no perceptible latency to video playback itself |
| Visual consistency | A single reference stylesheet per theme (dark/light); no colour hard-coded inside an individual widget |
| Accessibility | Existing keyboard shortcuts (V1 F11) remain functional in fullscreen, including while the controls are hidden |

---

## 6. Development plan

| Phase | Content | Expected output |
|---|---|---|
| Phase 13 — Fullscreen overlay | F21 | Working overlay controls, smooth hide/reappear behaviour |
| Phase 14 — Colour system | F25 | Configurable accent colour, applied to the existing stylesheets |
| Phase 15 — Component restyling | F22, F23, F24, F26 | Playback bar, playlist, settings, and mini-mode restyled per the F25 system |
| Phase 16 — Audio cover art | F27 | Cover art display for audio files, consistent across all three contexts (normal, fullscreen, mini-mode) |

**Note:** F25 must precede F22/F23/F24, since they consume the accent colour defined by F25. F21 (fullscreen) is independent and can be developed in parallel with, or before, the others.

---

## 7. Acceptance criteria (V3 Definition of Done)

1. Fullscreen displays overlay controls that hide after 5 seconds of mouse inactivity and reappear on the slightest movement
2. Controls remain permanently visible in fullscreen if playback is paused, or if the mouse is over the controls
3. The playback bar, the playlist grid, and settings follow a consistent colour system, with a configurable accent colour
4. Mini-mode visually reuses the same overlay controls as fullscreen (F21), with no component duplication
5. Audio files display their embedded cover art (or a generic icon as a fallback) in the video area, identically across the normal window, fullscreen, and mini-mode
6. No functional behaviour change is observable relative to V2 outside of F27 — only the appearance changes
7. 100% of existing V1/V2 tests pass with no change to their assertions

---

## 8. Identified risks

| Risk | Impact | Mitigation |
|---|---|---|
| Reusing `controls_widget.py` in both normal mode and as a fullscreen overlay may introduce positioning complexity | Medium | Clearly separate style (conditional QSS depending on mode) from logic (the same widget, unchanged signals) |
| Fade animation proving unreliable with `QPropertyAnimation`/`QGraphicsOpacityEffect` on macOS | Low | Plan a simple fallback (`show()`/`hide()` with no animation) if the animation proves unstable, rather than persisting with it |

---

## 9. Decisions made

1. **Fullscreen inactivity delay:** 5 seconds.
2. **Behaviour of the restyled Settings dialog (F24):** stays modal, blocking interaction with the rest of the application while it is open — unchanged from V2, only the styling changes.
3. **Mini-mode close button (F26):** minimises the application by default; configurable in the restyled Settings (F24) to switch to "Close the application" instead.
4. **Mini-mode controls auto-hide (F26):** identical to fullscreen — 5 seconds of inactivity.
5. **Fallback icon for missing audio cover art (F27):** tinted with the active accent colour (F25), not a static colour.

Every open question in this PRD is now settled — ready for V3 user stories.
