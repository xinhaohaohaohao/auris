from __future__ import annotations

from typing import Callable

try:
    from .lrc import build_lrc_text
    from .models import BuildResult, PipelineSettings, SegmentItem
    from .splitter import merge_short_sentences, normalize_text, split_sentences
    from .translator import translate_batch
    from .tts import synthesize_all
except ImportError:  # pragma: no cover
    from lrc import build_lrc_text
    from models import BuildResult, PipelineSettings, SegmentItem
    from splitter import merge_short_sentences, normalize_text, split_sentences
    from translator import translate_batch
    from tts import synthesize_all


ProgressCallback = Callable[[str], None]


def run_pipeline(
    text: str,
    *,
    settings: PipelineSettings,
    progress: ProgressCallback | None = None,
) -> BuildResult:
    _emit(progress, "Normalizing input text")
    normalized = normalize_text(text)
    if not normalized:
        raise ValueError("input text is empty after normalization")

    _emit(progress, "Splitting text into readable segments")
    split_segments = split_sentences(normalized, max_chars=settings.split_max_chars)
    merged_segments = merge_short_sentences(
        split_segments,
        min_chars=settings.split_min_chars,
        max_chars=settings.split_max_chars,
    )
    if not merged_segments:
        raise ValueError("no segments were produced from input text")

    segments = [
        SegmentItem(id=f"seg-{index:04d}", source_text=segment_text)
        for index, segment_text in enumerate(merged_segments, start=1)
    ]
    _emit(progress, f"Prepared {len(segments)} segments")

    warnings: list[str] = []
    _emit(progress, "Starting translation")
    outcomes = translate_batch(
        [segment.source_text for segment in segments],
        settings=settings,
        progress=progress,
    )
    for segment, outcome in zip(segments, outcomes, strict=True):
        segment.translated_text = outcome.translated_text
        segment.translation_error = outcome.error
        if outcome.error:
            warnings.append(f"{segment.id}: translation failed, English only. {outcome.error}")

    _emit(progress, "Starting TTS synthesis")
    audio_bytes, timestamps = synthesize_all(
        [segment.source_text for segment in segments],
        settings=settings,
        progress=progress,
    )
    for segment, (start_ms, end_ms) in zip(segments, timestamps, strict=True):
        segment.start_ms = start_ms
        segment.end_ms = end_ms

    _emit(progress, "Building LRC subtitles")
    lrc_text = build_lrc_text(segments)
    duration_ms = timestamps[-1][1] if timestamps else 0

    return BuildResult(
        segments=segments,
        audio_bytes=audio_bytes,
        lrc_text=lrc_text,
        duration_ms=duration_ms,
        warnings=warnings,
    )


def _emit(progress: ProgressCallback | None, message: str) -> None:
    if progress is not None:
        progress(message)
