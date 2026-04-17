"""FastAPI 後端：台語 ↔ 中文 雙向語音翻譯（Replicate proxy 版）

這支 server 不跑模型，只是代理呼叫 Replicate 上的 SeamlessM4T，
主要目的：把 REPLICATE_API_TOKEN 藏在後端，不讓 App 直接拿到。

啟動：
    export REPLICATE_API_TOKEN=r8_xxx
    python server.py
"""

from __future__ import annotations

import base64

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from translator import MODEL, translate_speech

app = FastAPI(title="Taigi ↔ Mandarin Translator (Replicate)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "backend": "replicate", "model": MODEL}


@app.post("/translate")
async def translate(
    audio: UploadFile = File(...),
    src_lang: str = Form("hok"),
    tgt_lang: str = Form("cmn"),
    with_speech: bool = Form(True),
) -> dict:
    raw = await audio.read()
    try:
        result = translate_speech(
            audio_bytes=raw,
            src_lang=src_lang,
            tgt_lang=tgt_lang,
            with_speech=with_speech,
            filename=audio.filename or "input.wav",
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:
        raise HTTPException(500, str(e))

    audio_b64 = base64.b64encode(result.audio_wav).decode() if result.audio_wav else None
    return {"text": result.text, "audio_b64": audio_b64}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000)
