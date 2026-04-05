from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

try:
    from .models import PipelineSettings
except ImportError:  # pragma: no cover
    from models import PipelineSettings


ProgressCallback = Callable[[str], None]


def synthesize_all(
    texts: list[str],
    *,
    settings: PipelineSettings,
    progress: ProgressCallback | None = None,
) -> tuple[bytes, list[tuple[int, int]]]:
    if not texts:
        raise ValueError("no texts provided for TTS")

    durations_ms: list[int] = []
    total = len(texts)

    with tempfile.TemporaryDirectory(prefix="auris_phase1_") as temp_dir:
        temp_root = Path(temp_dir)
        audio_paths: list[Path] = []

        for index, text in enumerate(texts, start=1):
            if _should_emit_progress(index=index, total=total):
                _emit(progress, f"Generating speech: {index}/{total}")

            output_path = temp_root / f"{index:04d}.mp3"
            _synthesize_segment(text, output_path=output_path, settings=settings)
            audio_paths.append(output_path)
            durations_ms.append(_probe_duration_ms(output_path, settings=settings))

        _emit(progress, "Merging audio files")
        merged_path = temp_root / "merged.mp3"
        _merge_audio_files(audio_paths, output_path=merged_path, settings=settings)
        audio_bytes = merged_path.read_bytes()

    _emit(progress, f"Speech generation finished: {total}/{total}")
    timestamps = _build_timestamps(durations_ms)
    return audio_bytes, timestamps


def _synthesize_segment(
    text: str,
    *,
    output_path: Path,
    settings: PipelineSettings,
) -> None:
    command = [
        settings.edge_tts_command,
        "--voice",
        settings.tts_voice,
        f"--rate={settings.tts_rate}",
        "--text",
        text,
        "--write-media",
        str(output_path),
    ]
    result = _run_command(command, missing_label="edge-tts", env_var_name="AURIS_EDGE_TTS_COMMAND")
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip() or "unknown edge-tts error"
        raise RuntimeError(f"edge-tts failed: {stderr}")


def _probe_duration_ms(path: Path, *, settings: PipelineSettings) -> int:
    command = [
        settings.ffprobe_command,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    result = _run_command(command, missing_label="ffprobe", env_var_name="AURIS_FFPROBE_COMMAND")
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip() or "unknown ffprobe error"
        raise RuntimeError(f"ffprobe failed: {stderr}")

    try:
        duration_seconds = float(result.stdout.strip())
    except ValueError as exc:
        raise RuntimeError("unable to parse ffprobe duration output") from exc

    return max(int(round(duration_seconds * 1000)), 1)


def _merge_audio_files(
    audio_paths: list[Path],
    *,
    output_path: Path,
    settings: PipelineSettings,
) -> None:
    concat_path = output_path.parent / "concat.txt"
    concat_lines = [_format_concat_line(path) for path in audio_paths]
    concat_path.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")

    command = [
        settings.ffmpeg_command,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_path),
        "-c",
        "copy",
        str(output_path),
    ]
    result = _run_command(command, missing_label="ffmpeg", env_var_name="AURIS_FFMPEG_COMMAND")
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip() or "unknown ffmpeg error"
        raise RuntimeError(f"ffmpeg failed: {stderr}")


def _run_command(
    command: list[str],
    *,
    missing_label: str,
    env_var_name: str,
) -> subprocess.CompletedProcess[str]:
    executable = command[0]
    if shutil.which(executable) is None and not Path(executable).exists():
        raise RuntimeError(
            f"{missing_label} not found. Add it to PATH or set {env_var_name} in .env to its full path."
        )

    try:
        return subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"{missing_label} not found. Add it to PATH or set {env_var_name} in .env to its full path."
        ) from exc


def _format_concat_line(path: Path) -> str:
    escaped_path = path.resolve().as_posix().replace("'", "'\\''")
    return "file '" + escaped_path + "'"


def _build_timestamps(durations_ms: list[int]) -> list[tuple[int, int]]:
    timestamps: list[tuple[int, int]] = []
    cursor = 0

    for duration in durations_ms:
        start_ms = cursor
        end_ms = cursor + max(duration, 1)
        timestamps.append((start_ms, end_ms))
        cursor = end_ms

    return timestamps


def _should_emit_progress(*, index: int, total: int) -> bool:
    if total <= 10:
        return True
    if index == 1 or index == total:
        return True
    step = max(total // 10, 1)
    return index % step == 0


def _emit(progress: ProgressCallback | None, message: str) -> None:
    if progress is not None:
        progress(message)
