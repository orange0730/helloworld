"""共用翻譯邏輯：透過 Replicate 呼叫 Meta 託管的 SeamlessM4T。

需要環境變數 REPLICATE_API_TOKEN（到 https://replicate.com/account/api-tokens 申請）。

Replicate 模型：cjwbw/seamless_communication
  https://replicate.com/cjwbw/seamless_communication
  同時支援 S2ST / S2TT / T2TT / T2ST / ASR，閩南語（Hokkien）是官方支援語言。
"""

from __future__ import annotations

import io
import os
from dataclasses import dataclass

import httpx
import replicate

MODEL = (
    "cjwbw/seamless_communication:"
    "668a4fec05a887143e5fe8d45df25ec4c794dd43169b9a11562309b2d45873b0"
)

LANG_NAME = {"hok": "Hokkien", "cmn": "Mandarin Chinese"}


@dataclass
class TranslateResult:
    text: str
    audio_wav: bytes | None


def _task(with_speech: bool) -> str:
    return (
        "S2ST (Speech to Speech translation)"
        if with_speech
        else "S2TT (Speech to Text translation)"
    )


def translate_speech(
    audio_bytes: bytes,
    src_lang: str,
    tgt_lang: str,
    with_speech: bool = True,
    filename: str = "input.wav",
) -> TranslateResult:
    if src_lang not in LANG_NAME or tgt_lang not in LANG_NAME:
        raise ValueError(f"lang must be in {set(LANG_NAME)}")
    if src_lang == tgt_lang:
        raise ValueError("src_lang and tgt_lang must differ")
    if not os.getenv("REPLICATE_API_TOKEN"):
        raise RuntimeError("REPLICATE_API_TOKEN not set")

    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename  # Replicate uses .name for MIME detection

    output = replicate.run(
        MODEL,
        input={
            "task_name": _task(with_speech),
            "input_audio": audio_file,
            "input_text_language": LANG_NAME[src_lang],
            "target_language_text_only": LANG_NAME[tgt_lang],
            "target_language_with_speech": LANG_NAME[tgt_lang],
        },
    )

    text = str(output.get("text_output") or output.get("text") or "").strip()

    audio_wav: bytes | None = None
    audio_ref = output.get("audio_output")
    if with_speech and audio_ref:
        audio_wav = _fetch_audio(audio_ref)

    return TranslateResult(text=text, audio_wav=audio_wav)


def _fetch_audio(ref) -> bytes:
    # Replicate may return a URL string or a FileOutput object with .read()
    if hasattr(ref, "read"):
        return ref.read()
    with httpx.Client(timeout=60) as client:
        r = client.get(str(ref))
        r.raise_for_status()
        return r.content
