"""台語（閩南語）→ 中文 語音翻譯 demo

使用 Meta SeamlessM4T v2（large）：
- 輸入：麥克風錄音或上傳音檔（台語 Hokkien）
- 輸出：中文（Mandarin）文字 + 合成語音

首次執行會從 Hugging Face 下載約 9GB 模型權重。
有 CUDA GPU 會自動使用；無則 fallback CPU（較慢）。
"""

from __future__ import annotations

import tempfile

import gradio as gr
import numpy as np
import torch
import torchaudio
from transformers import AutoProcessor, SeamlessM4Tv2Model

MODEL_ID = "facebook/seamless-m4t-v2-large"
SRC_LANG = "hok"  # Hokkien / 閩南語
TGT_LANG = "cmn"  # Mandarin Chinese / 中文
SAMPLE_RATE = 16000

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32

print(f"Loading {MODEL_ID} on {device} ...")
processor = AutoProcessor.from_pretrained(MODEL_ID)
model = SeamlessM4Tv2Model.from_pretrained(MODEL_ID, torch_dtype=dtype).to(device)
model.eval()


def _to_mono_16k(sr: int, waveform: np.ndarray) -> torch.Tensor:
    audio = torch.from_numpy(waveform).float()
    if audio.ndim == 1:
        audio = audio.unsqueeze(0)
    else:
        audio = audio.mean(dim=-1, keepdim=True).T
    if audio.abs().max() > 1.0:
        audio = audio / 32768.0
    if sr != SAMPLE_RATE:
        audio = torchaudio.functional.resample(audio, sr, SAMPLE_RATE)
    return audio


@torch.inference_mode()
def translate(audio: tuple[int, np.ndarray] | None, want_speech: bool):
    if audio is None:
        return "請先錄音或上傳音檔", None
    sr, waveform = audio
    audio_tensor = _to_mono_16k(sr, waveform).to(device)

    inputs = processor(audios=audio_tensor, sampling_rate=SAMPLE_RATE, return_tensors="pt").to(
        device, dtype=dtype if device == "cuda" else torch.float32
    )

    text_ids = model.generate(**inputs, tgt_lang=TGT_LANG, generate_speech=False)[0]
    mandarin_text = processor.decode(text_ids.squeeze().tolist(), skip_special_tokens=True)

    speech_path = None
    if want_speech:
        speech = model.generate(**inputs, tgt_lang=TGT_LANG, generate_speech=True)[0]
        speech_np = speech.cpu().numpy().squeeze()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            speech_path = f.name
        torchaudio.save(speech_path, torch.from_numpy(speech_np).unsqueeze(0), SAMPLE_RATE)

    return mandarin_text, speech_path


with gr.Blocks(title="台語 → 中文 語音翻譯") as demo:
    gr.Markdown("# 台語（閩南語）→ 中文 語音翻譯\n" "Powered by Meta SeamlessM4T v2 large")
    with gr.Row():
        audio_in = gr.Audio(sources=["microphone", "upload"], type="numpy", label="台語音檔")
        with gr.Column():
            want_speech = gr.Checkbox(label="同時合成中文語音", value=True)
            btn = gr.Button("翻譯", variant="primary")
    text_out = gr.Textbox(label="中文文字", lines=3)
    audio_out = gr.Audio(label="中文語音", type="filepath")
    btn.click(translate, inputs=[audio_in, want_speech], outputs=[text_out, audio_out])


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0")
