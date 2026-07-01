"""Episode audio assembly (ffmpeg): optional intro/outro, loudness normalization, MP3 encode.

Runs on the VPS when the home worker uploads raw narration. The ffmpeg argument builder is pure
so it can be unit-tested without invoking ffmpeg.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

# EBU R128 loudness target appropriate for spoken-word podcasts.
LOUDNORM = "loudnorm=I=-16:TP=-1.5:LRA=11"


def build_ffmpeg_args(
    input_path: str,
    output_path: str,
    *,
    intro: str | None = None,
    outro: str | None = None,
    normalize: bool = True,
    bitrate: str = "128k",
) -> list[str]:
    """Build the ffmpeg command to assemble [intro +] narration [+ outro] → normalized MP3."""
    files: list[str] = []
    if intro:
        files.append(str(intro))
    files.append(str(input_path))
    if outro:
        files.append(str(outro))

    args = ["ffmpeg", "-y"]
    for f in files:
        args += ["-i", f]

    n = len(files)
    if n > 1:
        chain = "".join(f"[{i}:a]" for i in range(n)) + f"concat=n={n}:v=0:a=1[c]"
    else:
        chain = "[0:a]anull[c]"
    last = "[c]"
    if normalize:
        chain += f";[c]{LOUDNORM}[out]"
        last = "[out]"

    args += [
        "-filter_complex",
        chain,
        "-map",
        last,
        "-c:a",
        "libmp3lame",
        "-b:a",
        bitrate,
        str(output_path),
    ]
    return args


def probe_duration(path: str) -> float:
    """Return audio duration in seconds via ffprobe (0.0 if unknown)."""
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)],
        capture_output=True,
        text=True,
    )
    data = json.loads(out.stdout or "{}")
    try:
        return float(data.get("format", {}).get("duration", 0.0))
    except (TypeError, ValueError):
        return 0.0


def assemble(
    raw_path: str,
    output_path: str,
    *,
    intro: str | None = None,
    outro: str | None = None,
) -> tuple[float, int]:
    """Assemble + normalize + encode. Returns (duration_seconds, size_bytes)."""
    args = build_ffmpeg_args(raw_path, output_path, intro=intro, outro=outro)
    subprocess.run(args, check=True, capture_output=True)
    return probe_duration(output_path), Path(output_path).stat().st_size
