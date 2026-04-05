from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SegmentItem:
    id: str
    source_text: str
    translated_text: str | None = None
    start_ms: int | None = None
    end_ms: int | None = None
    translation_error: str | None = None


@dataclass(slots=True)
class TranslationOutcome:
    translated_text: str | None = None
    error: str | None = None


@dataclass(slots=True)
class PipelineSettings:
    tencent_secret_id: str
    tencent_secret_key: str
    tencent_region: str
    source_lang: str = "en"
    target_lang: str = "zh"
    tencent_host: str = "tmt.tencentcloudapi.com"
    tencent_action: str = "TextTranslate"
    tencent_version: str = "2018-03-21"
    tencent_project_id: int = 0
    translation_rps: int = 5
    translation_timeout_s: int = 15
    translation_max_chars: int = 5800
    tts_voice: str = "en-US-AriaNeural"
    tts_rate: str = "+0%"
    edge_tts_command: str = "edge-tts"
    ffmpeg_command: str = "ffmpeg"
    ffprobe_command: str = "ffprobe"
    split_max_chars: int = 120
    split_min_chars: int = 25


@dataclass(slots=True)
class BuildResult:
    segments: list[SegmentItem]
    audio_bytes: bytes
    lrc_text: str
    duration_ms: int
    warnings: list[str] = field(default_factory=list)
