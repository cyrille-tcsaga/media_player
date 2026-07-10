import hashlib
import re
import shutil
import subprocess
from pathlib import Path

from core.models import MediaItem

# Cf. core/playlist_persistence.py / core/settings_manager.py : même convention
# cross-platform (~/.media_player/...) plutôt que le chemin macOS-spécifique
# suggéré par le PRD V2 (~/Library/Caches/MediaPlayer/thumbnails/).
DEFAULT_THUMBNAIL_CACHE_DIR = Path.home() / ".media_player" / "thumbnails"

FFMPEG_TIMEOUT_SECONDS = 10
THUMBNAIL_POSITION_RATIO = 0.10

_DURATION_PATTERN = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")


def generate_thumbnail(media_item: MediaItem, cache_dir: Path) -> Path | None:
    if not media_item.file_path.exists():
        return None

    cache_dir.mkdir(parents=True, exist_ok=True)
    output_path = _cache_path_for(media_item.file_path, cache_dir)
    if output_path.exists():
        # Déjà généré lors d'un précédent lancement : pas de régénération.
        return output_path

    ffmpeg_path = shutil.which("ffmpeg") or "ffmpeg"

    duration_seconds = _probe_duration_seconds(media_item.file_path, ffmpeg_path)
    if duration_seconds is None or duration_seconds <= 0:
        return None

    # Position relative (10% par défaut) plutôt que 0, souvent un écran noir
    # en tout début de vidéo.
    timestamp = duration_seconds * THUMBNAIL_POSITION_RATIO

    try:
        result = subprocess.run(
            [
                ffmpeg_path,
                "-ss",
                f"{timestamp:.3f}",
                "-i",
                str(media_item.file_path),
                "-frames:v",
                "1",
                "-y",
                str(output_path),
            ],
            capture_output=True,
            timeout=FFMPEG_TIMEOUT_SECONDS,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None

    if result.returncode != 0 or not output_path.exists():
        return None

    return output_path


def _probe_duration_seconds(media_path: Path, ffmpeg_path: str) -> float | None:
    # ffmpeg -i sans fichier de sortie termine en erreur mais imprime la durée
    # sur stderr — évite de dépendre de ffprobe, non embarqué par US-110.
    try:
        result = subprocess.run(
            [ffmpeg_path, "-i", str(media_path)],
            capture_output=True,
            text=True,
            timeout=FFMPEG_TIMEOUT_SECONDS,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None

    match = _DURATION_PATTERN.search(result.stderr)
    if match is None:
        return None

    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def _cache_path_for(media_path: Path, cache_dir: Path) -> Path:
    digest = hashlib.sha256(str(media_path.resolve()).encode("utf-8")).hexdigest()
    return cache_dir / f"{digest}.jpg"
