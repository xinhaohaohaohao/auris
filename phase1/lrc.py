from __future__ import annotations

try:
    from .models import SegmentItem
except ImportError:  # pragma: no cover
    from models import SegmentItem


def format_lrc_time(ms: int) -> str:
    total_centiseconds = max(ms, 0) // 10
    minutes, centiseconds_total = divmod(total_centiseconds, 6000)
    seconds, centiseconds = divmod(centiseconds_total, 100)
    return f"[{minutes:02d}:{seconds:02d}.{centiseconds:02d}]"


def build_lrc_text(segments: list[SegmentItem]) -> str:
    lines: list[str] = []

    for segment in segments:
        if segment.start_ms is None:
            continue

        timestamp = format_lrc_time(segment.start_ms)
        lines.append(f"{timestamp}{segment.source_text}")
        if segment.translated_text:
            lines.append(f"{timestamp}{segment.translated_text}")

    return "\n".join(lines) + ("\n" if lines else "")
