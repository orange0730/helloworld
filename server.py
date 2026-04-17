"""FastAPI 後端：台語 ↔ 中文 雙向語音翻譯

POST /translate   multipart form:
    audio      : 16-bit PCM WAV，建議 16kHz 單聲道
    src_lang   : hok | cmn
    tgt_lang   : cmn | hok
    with_speech: true | false   是否合成目標語言語音

Response JSON:
    { "text": "...", "audio_b64": "<wav base64 或 null>" }
"""

from __future__ import annotations

import base64
import io

import torch
import torchaudio
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from transformers import AutoProcessor, SeamlessM4Tv2Model

MODEL_ID = "facebook/seamless-m4t-v2-large"
SAMPLE_RATE = 16000
SUPPORTED = {"hok", "cmn"}

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32

print(f"Loading {MODEL_ID} on {device} ...")
processor = AutoProcessor.from_pretrained(MODEL_ID)
model = SeamlessM4Tv2Model.from_pretrained(MODEL_ID, torch_dtype=dtype).to(device)
model.eval()

app = FastAPI(title="Taigi ↔ Mandarin Translator")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load_wav(raw: bytes) -> torch.Tensor:
    waveform, sr = torchaudio.load(io.BytesIO(raw))
    if sr != SAMPLE_RATE:
        waveform = torchaudio.functional.resample(waveform, sr, SAMPLE_RATE)
    return waveform.mean(dim=0, keepdim=True)


def _encode_wav(waveform: torch.Tensor) -> str:
    buf = io.BytesIO()
    torchaudio.save(buf, waveform, SAMPLE_RATE, format="wav")
    return base64.b64encode(buf.getvalue()).decode()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "device": device, "model": MODEL_ID}


@app.post("/translate")
async def translate(
    audio: UploadFile = File(...),
    src_lang: str = Form("hok"),
    tgt_lang: str = Form("cmn"),
    with_speech: bool = Form(True),
) -> dict:
    if src_lang not in SUPPORTED or tgt_lang not in SUPPORTED:
        raise HTTPException(400, f"lang must be one of {SUPPORTED}")
    if src_lang == tgt_lang:
        raise HTTPException(400, "src_lang and tgt_lang must differ")

    waveform = _load_wav(await audio.read()).to(device)
    inputs = processor(
        audios=waveform, sampling_rate=SAMPLE_RATE, return_tensors="pt"
    ).to(device, dtype=dtype if device == "cuda" else torch.float32)

    with torch.inference_mode():
        text_ids = model.generate(**inputs, tgt_lang=tgt_lang, generate_speech=False)[0]
        text = processor.decode(text_ids.squeeze().tolist(), skip_special_tokens=True)

        audio_b64: str | None = None
        if with_speech:
            speech = model.generate(**inputs, tgt_lang=tgt_lang, generate_speech=True)[0]
            audio_b64 = _encode_wav(speech.cpu().float().unsqueeze(0))

    return {"text": text, "audio_b64": audio_b64}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000)
