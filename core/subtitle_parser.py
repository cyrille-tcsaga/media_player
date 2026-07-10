import re
from pathlib import Path

from core.models import SubtitleEntry

_TIMECODE_PATTERN = re.compile(
    r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})"
)


def parse_srt(path: Path) -> list[SubtitleEntry]:
    if not path.exists():
        return []

    raw_text = _read_text_with_fallback_encoding(path)
    if raw_text is None:
        return []

    entries: list[SubtitleEntry] = []
    # Blocs séparés par une ligne vide (SRT standard).
    blocks = re.split(r"\r?\n\r?\n", raw_text.strip())

    for block in blocks:
        entry = _parse_block(block)
        if entry is not None:
            entries.append(entry)

    return entries


def _read_text_with_fallback_encoding(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        pass
    except OSError:
        return None

    try:
        # cp1252 (superset usuel de Latin-1 sur Windows) : repli simple plutôt
        # qu'une détection d'encodage via une bibliothèque tierce, superflue
        # pour un format aussi simple que .srt.
        return path.read_text(encoding="cp1252")
    except OSError:
        return None


def _parse_block(block: str) -> SubtitleEntry | None:
    lines = block.splitlines()
    if not lines:
        return None

    # La première ligne est normalement un index numérique (ignoré) ; certains
    # fichiers légèrement non conformes omettent cet index.
    timecode_line_index = 0
    if not _TIMECODE_PATTERN.search(lines[0]) and len(lines) > 1:
        timecode_line_index = 1

    if timecode_line_index >= len(lines):
        return None

    match = _TIMECODE_PATTERN.search(lines[timecode_line_index])
    if match is None:
        return None

    start_ms = _to_ms(*match.groups()[0:4])
    end_ms = _to_ms(*match.groups()[4:8])
    if end_ms < start_ms:
        return None

    text = "\n".join(lines[timecode_line_index + 1 :]).strip()
    if not text:
        return None

    return SubtitleEntry(start_ms=start_ms, end_ms=end_ms, text=text)


def _to_ms(hours: str, minutes: str, seconds: str, millis: str) -> int:
    return int(hours) * 3_600_000 + int(minutes) * 60_000 + int(seconds) * 1_000 + int(millis)
