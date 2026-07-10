# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

This repository currently contains **only planning documents** — no source code exists yet:

- `docs/PRD_Lecteur_Media_PyQt6.md` — the product/technical spec (French, with a fuller English restatement in the second half of the same file).
- `docs/USER_STORIES_Lecteur_Media_PyQt6.md` — a sequential backlog of user stories (`US-PPNN`, `PP` = phase 00–06) meant to be executed **in order, one story at a time**, by Claude Code. Also bilingual (French first, English restatement second).

Read both files before starting any implementation work — they are the source of truth for scope, architecture, and acceptance criteria. Do not start coding without them; the guidance below summarizes their content but the docs themselves take precedence if anything conflicts.

## What this project is

A local, single-user desktop audio/video player built with **Python 3.11+ / PyQt6 / QtMultimedia** (`QMediaPlayer`, `QAudioOutput`, `QVideoWidget`). It's a personal portfolio project, not a VLC competitor.

**Explicitly out of scope** (don't implement even if it seems like a natural extension): network streaming (HTTP/RTSP), transcoding, video editing, third-party plugins, cloud sync/multi-device, DRM, advanced audio EQ, recording/capture. V2 features (playlist persistence, repeat/shuffle, themes, thumbnails, subtitles, playback speed, mini-mode) are deferred — do not pull them into MVP work without an explicit scope revision.

## Working through the backlog

`docs/USER_STORIES_Lecteur_Media_PyQt6.md` is designed to be executed story by story:

- **Do not advance to the next story until the current story's acceptance criteria are all verified, including passing tests.**
- One atomic commit per story, message = story ID + title (e.g. `US-020 — Implement the playback engine (core)`).
- Each story lists its acceptance criteria, files involved, and dependencies on prior stories — check dependencies before starting a story out of order.
- Several stories carry a "Notes for Claude Code" callout with story-specific constraints (e.g. don't add pytest until US-013, don't wire `PlayerEngine` into the main window until US-022). Read the note for the story you're on.

## Architecture (lightweight MVVM)

Target folder structure, defined in PRD section 4.2 — follow it exactly, do not reorganize it even if another layout seems more idiomatic, since later stories reference these exact paths:

```
media_player/
├── main.py                  # Entry point, bootstraps the Qt Application
├── core/
│   ├── player_engine.py     # Wrapper around QMediaPlayer (pure business logic)
│   ├── playlist_manager.py  # Playlist management (add/remove/navigate)
│   └── models.py            # Dataclasses: MediaItem, PlaybackState, etc.
├── ui/
│   ├── main_window.py       # QMainWindow, assembles the widgets
│   ├── controls_widget.py   # Play/pause/stop buttons
│   ├── progress_widget.py   # Progress slider + time labels
│   ├── playlist_widget.py   # Custom QListWidget for the playlist
│   ├── volume_widget.py     # Volume slider + mute/unmute button
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

**Non-negotiable rule: `core/` must never import anything from `PyQt6.QtWidgets`.** Only `ui/` touches widgets. `viewmodels/` bridges the two via Qt signals/slots (`pyqtSignal`), so `core/` can be unit-tested without instantiating any window. Before finishing any story that touches `core/`, verify no `PyQt6.QtWidgets` import crept in.

Data flow example (play/pause): widget emits a signal (`play_requested`) → `player_viewmodel.py` calls `player_engine.play()` → engine delegates to `QMediaPlayer.play()` → Qt emits `playbackStateChanged` → ViewModel updates its exposed state → `main_window.py` reacts (e.g. updates the play/pause icon). New UI-facing state changes should follow this same one-directional signal path, not update widgets directly from `core/`.

If a new UI file is added beyond what's listed above (e.g. `ui/volume_widget.py`), update PRD section 4.2 in the same change so the architecture doc stays in sync with the code.

## Commands

Not yet scaffolded (no `venv`, `requirements.txt`, or test suite exists at present — these are created in US-000/US-012/US-013). Once they exist, per the PRD/backlog:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt        # runtime deps (PyQt6, ...)
pip install -r requirements-dev.txt    # dev-only deps (pytest, pytest-qt, ruff), kept separate so end users don't need them
pytest                                 # full test suite
pytest tests/test_player_engine.py     # single test file
pytest --fixtures | grep qtbot         # sanity-check pytest-qt's qtbot fixture is registered
ruff check .                           # lint
```

CI runs on `ubuntu-latest`; since `pytest-qt` instantiates real widgets, the workflow needs a virtual X server (`xvfb-run`, or an equivalent headless-display GitHub Action).

Packaging (Phase 6) uses `PyInstaller`. On macOS specifically, verify after packaging that FFmpeg libraries are actually embedded in the `.app` bundle (e.g. via `otool -L` on the final binary) rather than merely present on the build machine.

## Cross-cutting gotchas from the backlog

- **Codec/backend support is platform-dependent.** Qt6 Multimedia defaults to an FFmpeg backend on macOS since Qt 6.5 (fallback to native `darwin` backend via `QT_MEDIA_BACKEND`), but Windows may use Media Foundation instead. Always log the active backend at startup rather than assuming.
- **Seek slider vs. auto-update conflict:** track an internal `is_seeking: bool` flag on the progress widget, set `True` on `sliderPressed` / `False` on `sliderReleased`, to avoid the slider fighting the user while they drag.
- **Keyboard shortcuts:** use `QShortcut` + `QKeySequence` rather than overriding `keyPressEvent`, for correct native focus-conflict handling.
- **Drag & drop:** filter file extensions in `dropEvent` before adding to the playlist, not after — don't let `PlaylistManager` see invalid files.
- **Error handling:** map `QMediaPlayer.Error` values (`ResourceError`, `FormatError`, `NetworkError`, `AccessDeniedError`) to explicit user-facing messages via a lookup table, not by displaying the raw enum.
- **Test coverage target is `core/` >= 70%.** Don't pad it with assertion-free tests — prioritize real error branches (missing file, empty playlist, etc.).
- Test fixtures should stay small (e.g. a 2-second silent audio clip) rather than committing large binary assets to the public repo; document how to (re)generate them if they can't be generated in-session.
