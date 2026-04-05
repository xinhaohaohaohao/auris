from __future__ import annotations

import hashlib
import hmac
import json
import time
from collections import deque
from datetime import datetime, timezone
from typing import Callable, Deque

import requests

try:
    from .models import PipelineSettings, TranslationOutcome
except ImportError:  # pragma: no cover
    from models import PipelineSettings, TranslationOutcome

_REQUEST_TIMES: Deque[float] = deque()
ProgressCallback = Callable[[str], None]


def translate_batch(
    texts: list[str],
    *,
    settings: PipelineSettings,
    progress: ProgressCallback | None = None,
) -> list[TranslationOutcome]:
    outcomes: list[TranslationOutcome] = []
    total = len(texts)

    for index, text in enumerate(texts, start=1):
        if _should_emit_progress(index=index, total=total):
            _emit(progress, f"Translating segments: {index}/{total}")

        if not text.strip():
            outcomes.append(TranslationOutcome(translated_text=""))
            continue

        try:
            _wait_for_rate_limit(rps=settings.translation_rps)
            translated_text = _translate_one(text, settings=settings)
            outcomes.append(TranslationOutcome(translated_text=translated_text))
        except Exception as exc:  # noqa: BLE001
            outcomes.append(TranslationOutcome(error=str(exc)))

    _emit(progress, f"Translation finished: {total}/{total}")
    return outcomes


def _translate_one(text: str, *, settings: PipelineSettings) -> str:
    if len(text) > settings.translation_max_chars:
        raise ValueError(
            f"text too long for a single translation request: {len(text)} chars"
        )

    payload = {
        "SourceText": text,
        "Source": settings.source_lang,
        "Target": settings.target_lang,
        "ProjectId": settings.tencent_project_id,
    }
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    timestamp = int(time.time())
    headers = _build_tc3_headers(payload_json=payload_json, timestamp=timestamp, settings=settings)

    response = requests.post(
        f"https://{settings.tencent_host}/",
        data=payload_json.encode("utf-8"),
        headers=headers,
        timeout=settings.translation_timeout_s,
    )
    response.raise_for_status()

    response_json = response.json()
    response_body = response_json.get("Response", {})
    error = response_body.get("Error")
    if error:
        code = error.get("Code", "UnknownError")
        message = error.get("Message", "unknown translation error")
        raise RuntimeError(f"{code}: {message}")

    translated = response_body.get("TargetText")
    if not isinstance(translated, str):
        raise RuntimeError("missing TargetText in translation response")

    return translated.strip()


def _wait_for_rate_limit(*, rps: int) -> None:
    if rps <= 0:
        return

    now = time.monotonic()
    while _REQUEST_TIMES and now - _REQUEST_TIMES[0] >= 1:
        _REQUEST_TIMES.popleft()

    if len(_REQUEST_TIMES) >= rps:
        sleep_for = 1 - (now - _REQUEST_TIMES[0])
        if sleep_for > 0:
            time.sleep(sleep_for)

    now = time.monotonic()
    while _REQUEST_TIMES and now - _REQUEST_TIMES[0] >= 1:
        _REQUEST_TIMES.popleft()

    _REQUEST_TIMES.append(time.monotonic())


def _build_tc3_headers(
    *,
    payload_json: str,
    timestamp: int,
    settings: PipelineSettings,
) -> dict[str, str]:
    service = "tmt"
    host = settings.tencent_host
    algorithm = "TC3-HMAC-SHA256"
    content_type = "application/json; charset=utf-8"
    signed_headers = "content-type;host"
    date = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d")

    canonical_request = "\n".join(
        [
            "POST",
            "/",
            "",
            f"content-type:{content_type}\n" f"host:{host}\n",
            signed_headers,
            hashlib.sha256(payload_json.encode("utf-8")).hexdigest(),
        ]
    )

    credential_scope = f"{date}/{service}/tc3_request"
    string_to_sign = "\n".join(
        [
            algorithm,
            str(timestamp),
            credential_scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
        ]
    )

    secret_date = _hmac_sha256(date.encode("utf-8"), f"TC3{settings.tencent_secret_key}".encode("utf-8"))
    secret_service = _hmac_sha256(service.encode("utf-8"), secret_date)
    secret_signing = _hmac_sha256(b"tc3_request", secret_service)
    signature = hmac.new(
        secret_signing,
        string_to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    authorization = (
        f"{algorithm} "
        f"Credential={settings.tencent_secret_id}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )

    return {
        "Authorization": authorization,
        "Content-Type": content_type,
        "Host": host,
        "X-TC-Action": settings.tencent_action,
        "X-TC-Region": settings.tencent_region,
        "X-TC-Timestamp": str(timestamp),
        "X-TC-Version": settings.tencent_version,
    }


def _hmac_sha256(message: bytes, secret: bytes) -> bytes:
    return hmac.new(secret, message, hashlib.sha256).digest()


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
