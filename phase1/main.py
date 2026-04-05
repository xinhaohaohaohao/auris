from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

try:
    from .fetcher import FetchResult, fetch_article, guess_stem_from_url
    from .models import BuildResult, PipelineSettings
    from .pipeline import run_pipeline
except ImportError:  # pragma: no cover
    from fetcher import FetchResult, fetch_article, guess_stem_from_url
    from models import BuildResult, PipelineSettings
    from pipeline import run_pipeline


@dataclass(slots=True)
class InputPayload:
    text: str
    stem: str | None = None
    fetched: FetchResult | None = None


ProgressCallback = Callable[[str], None]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Auris phase 1 prototype")
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--file", type=Path, help="path to a .txt or .md file")
    source_group.add_argument("--text", help="raw English text")
    source_group.add_argument("--url", help="URL of an article page to fetch")

    parser.add_argument("--out-dir", type=Path, default=Path("output"), help="directory for mp3 and lrc outputs")
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path(os.getenv("AURIS_SOURCE_DIR", "originals")),
        help="directory for saving fetched source articles",
    )
    parser.add_argument("--stem", help="output file stem, defaults to input file name or page title")
    parser.add_argument(
        "--save-format",
        choices=("txt", "md"),
        default=os.getenv("AURIS_FETCH_SAVE_FORMAT", "txt"),
        help="format used when saving fetched webpage content",
    )
    parser.add_argument(
        "--fetch-timeout",
        type=int,
        default=int(os.getenv("AURIS_FETCH_TIMEOUT_S", "20")),
        help="timeout in seconds when fetching webpages",
    )
    parser.add_argument(
        "--fetch-only",
        action="store_true",
        help="only fetch and save webpage content, do not run translation/TTS pipeline",
    )
    parser.add_argument("--voice", default=os.getenv("AURIS_TTS_VOICE", "en-US-AriaNeural"))
    parser.add_argument("--rate", default=os.getenv("AURIS_TTS_RATE", "+0%"))
    parser.add_argument(
        "--split-max-chars",
        type=int,
        default=int(os.getenv("AURIS_SPLIT_MAX_CHARS", "120")),
    )
    parser.add_argument(
        "--split-min-chars",
        type=int,
        default=int(os.getenv("AURIS_SPLIT_MIN_CHARS", "25")),
    )
    parser.add_argument(
        "--translation-rps",
        type=int,
        default=int(os.getenv("AURIS_TRANSLATION_RPS", "5")),
    )
    parser.add_argument(
        "--translation-max-chars",
        type=int,
        default=int(os.getenv("AURIS_TRANSLATION_MAX_CHARS", "5800")),
    )
    parser.add_argument(
        "--region",
        default=os.getenv("TENCENT_REGION", "ap-beijing"),
        help="Tencent Cloud region for the TMT API",
    )
    parser.add_argument(
        "--edge-tts-command",
        default=os.getenv("AURIS_EDGE_TTS_COMMAND", "edge-tts"),
    )
    parser.add_argument(
        "--ffmpeg-command",
        default=os.getenv("AURIS_FFMPEG_COMMAND", "ffmpeg"),
    )
    parser.add_argument(
        "--ffprobe-command",
        default=os.getenv("AURIS_FFPROBE_COMMAND", "ffprobe"),
    )
    return parser.parse_args()


def load_input_text(args: argparse.Namespace, *, progress: ProgressCallback | None = None) -> InputPayload:
    if args.text:
        if progress is not None:
            progress("Loaded inline text input")
        return InputPayload(text=args.text, stem=None)

    if args.url:
        if progress is not None:
            progress(f"Fetching webpage: {args.url}")
        fetched = fetch_article(args.url, timeout_s=args.fetch_timeout)
        if progress is not None:
            progress(f"Fetched webpage and extracted article: {fetched.title}")
        return InputPayload(
            text=fetched.text_content,
            stem=fetched.title or guess_stem_from_url(args.url),
            fetched=fetched,
        )

    input_path: Path = args.file.resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"input file does not exist: {input_path}")

    if progress is not None:
        progress(f"Reading source file: {input_path.name}")

    suffix = input_path.suffix.lower()
    raw_text = _read_utf8_text(input_path)
    if suffix == ".txt":
        return InputPayload(text=raw_text, stem=input_path.stem)
    if suffix == ".md":
        return InputPayload(text=_extract_markdown_text(raw_text), stem=input_path.stem)

    raise ValueError("only .txt and .md files are supported in phase 1")


def load_settings(args: argparse.Namespace) -> PipelineSettings:
    secret_id = os.getenv("TENCENT_SECRET_ID", "").strip()
    secret_key = os.getenv("TENCENT_SECRET_KEY", "").strip()
    if not secret_id or not secret_key:
        raise RuntimeError(
            "missing Tencent credentials: set TENCENT_SECRET_ID and TENCENT_SECRET_KEY"
        )

    return PipelineSettings(
        tencent_secret_id=secret_id,
        tencent_secret_key=secret_key,
        tencent_region=args.region,
        translation_rps=args.translation_rps,
        translation_max_chars=args.translation_max_chars,
        tts_voice=args.voice,
        tts_rate=args.rate,
        split_max_chars=args.split_max_chars,
        split_min_chars=args.split_min_chars,
        edge_tts_command=args.edge_tts_command,
        ffmpeg_command=args.ffmpeg_command,
        ffprobe_command=args.ffprobe_command,
    )


def write_outputs(
    result: BuildResult,
    *,
    out_dir: Path,
    stem: str,
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)

    audio_path = out_dir / f"{stem}.mp3"
    lrc_path = out_dir / f"{stem}.lrc"

    audio_path.write_bytes(result.audio_bytes)
    lrc_path.write_text(result.lrc_text, encoding="utf-8")
    return audio_path, lrc_path


def write_fetched_content(
    fetched: FetchResult,
    *,
    source_dir: Path,
    stem: str,
    save_format: str,
) -> Path:
    source_dir.mkdir(parents=True, exist_ok=True)

    if save_format == "md":
        path = source_dir / f"{stem}.md"
        path.write_text(fetched.markdown_content, encoding="utf-8")
        return path

    path = source_dir / f"{stem}.txt"
    path.write_text(fetched.text_content, encoding="utf-8")
    return path


def main() -> int:
    args = parse_args()
    progress = _make_progress_printer()

    progress("Starting conversion")
    payload = load_input_text(args, progress=progress)
    stem = _sanitize_stem(args.stem or payload.stem or "auris-output")

    if payload.fetched is not None:
        progress(f"Saving fetched source article to {args.source_dir}")
        fetched_path = write_fetched_content(
            payload.fetched,
            source_dir=args.source_dir,
            stem=stem,
            save_format=args.save_format,
        )
        print(f"fetched: {fetched_path}")
        if args.fetch_only:
            progress("Fetch-only mode completed")
            return 0

    text = payload.text
    settings = load_settings(args)
    result = run_pipeline(text, settings=settings, progress=progress)

    progress(f"Writing mp3 and lrc to {args.out_dir}")
    audio_path, lrc_path = write_outputs(result, out_dir=args.out_dir, stem=stem)

    print(f"segments: {len(result.segments)}")
    print(f"duration_ms: {result.duration_ms}")
    print(f"audio: {audio_path}")
    print(f"lrc: {lrc_path}")
    for warning in result.warnings:
        print(f"warning: {warning}")

    progress("Completed")
    return 0


def _make_progress_printer() -> ProgressCallback:
    def emit(message: str) -> None:
        print(f"[progress] {message}", flush=True)

    return emit


def _read_utf8_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("utf-8", b"", 0, 1, f"unable to decode file: {path}")


def _extract_markdown_text(markdown_text: str) -> str:
    text = re.sub(r"```.*?```", " ", markdown_text, flags=re.DOTALL)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    text = text.replace("**", "").replace("__", "").replace("*", "").replace("_", "")
    text = re.sub(r">\s*", "", text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n\n".join(lines)


def _sanitize_stem(stem: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-")
    return sanitized or "auris-output"


if __name__ == "__main__":
    raise SystemExit(main())
