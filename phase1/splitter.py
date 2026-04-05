from __future__ import annotations

import re

PRIMARY_SPLIT_RE = re.compile(r"(?<=[.!?;:])\s+")
SECONDARY_SPLIT_RE = re.compile(r"(?<=[,)\]])\s+|(?<=[-])\s+")
WORD_RE = re.compile(r"\S+")


def normalize_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{2,}", "\n\n", normalized)
    return normalized.strip()


def split_sentences(text: str, *, max_chars: int) -> list[str]:
    chunks = _split_with_regex(text, PRIMARY_SPLIT_RE)
    segments: list[str] = []

    for chunk in chunks:
        if len(chunk) <= max_chars:
            segments.append(chunk)
            continue

        secondary_chunks = _split_with_regex(chunk, SECONDARY_SPLIT_RE)
        for secondary in secondary_chunks:
            if len(secondary) <= max_chars:
                segments.append(secondary)
            else:
                segments.extend(_split_by_words(secondary, max_chars=max_chars))

    return [segment for segment in segments if segment]


def merge_short_sentences(
    sentences: list[str],
    *,
    min_chars: int,
    max_chars: int,
) -> list[str]:
    merged: list[str] = []

    for sentence in sentences:
        cleaned = sentence.strip()
        if not cleaned:
            continue

        if not merged:
            merged.append(cleaned)
            continue

        previous = merged[-1]
        combined = f"{previous} {cleaned}".strip()

        if len(previous) < min_chars and len(combined) <= max_chars:
            merged[-1] = combined
            continue

        if len(cleaned) < min_chars and len(combined) <= max_chars:
            merged[-1] = combined
            continue

        merged.append(cleaned)

    return merged


def _split_with_regex(text: str, pattern: re.Pattern[str]) -> list[str]:
    pieces = [piece.strip() for piece in pattern.split(text) if piece.strip()]
    return pieces or ([text.strip()] if text.strip() else [])


def _split_by_words(text: str, *, max_chars: int) -> list[str]:
    words = WORD_RE.findall(text)
    if not words:
        return []

    parts: list[str] = []
    current: list[str] = []
    current_len = 0

    for word in words:
        projected_len = current_len + len(word) + (1 if current else 0)
        if current and projected_len > max_chars:
            parts.append(" ".join(current).strip())
            current = [word]
            current_len = len(word)
            continue

        current.append(word)
        current_len = projected_len

    if current:
        parts.append(" ".join(current).strip())

    return parts
