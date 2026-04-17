"""台語 ↔ 中文 語音翻譯 Gradio demo（Replicate API 版）

透過 Replicate 呼叫 Meta SeamlessM4T，無需本機 GPU。
先設好環境變數：
    export REPLICATE_API_TOKEN=r8_xxx
"""

from __future__ import annotations

import io
import tempfile

import gradio as gr
import numpy as np
import soundfile as sf

from translator import translate_speech

LANG_CHOICES = [("台語 Hokkien", "hok"), ("中文 Mandarin", "cmn")]


def _numpy_to_wav_bytes(sr: int, waveform: np.ndarray) -> bytes:
    if waveform.ndim == 2:
        waveform = waveform.mean(axis=1)
    if waveform.dtype != np.int16:
        peak = np.max(np.abs(waveform)) or 1.0
        waveform = np.int16(waveform / peak * 32767)
    buf = io.BytesIO()
    sf.write(buf, waveform, sr, format="WAV", subtype="PCM_16")
    return buf.getvalue()


def translate(audio, src: str, tgt: str, want_speech: bool):
    if audio is None:
        return "請先錄音或上傳音檔", None
    sr, waveform = audio
    wav_bytes = _numpy_to_wav_bytes(sr, waveform)

    result = translate_speech(
        audio_bytes=wav_bytes,
        src_lang=src,
        tgt_lang=tgt,
        with_speech=want_speech,
    )

    out_path = None
    if result.audio_wav:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(result.audio_wav)
            out_path = f.name

    return result.text, out_path


with gr.Blocks(title="台語 ↔ 中文 語音翻譯") as demo:
    gr.Markdown(
        "# 台語 ↔ 中文 語音翻譯\n"
        "Meta SeamlessM4T v2，透過 Replicate API（需設 `REPLICATE_API_TOKEN`）"
    )
    with gr.Row():
        src = gr.Dropdown(LANG_CHOICES, value="hok", label="來源語言")
        tgt = gr.Dropdown(LANG_CHOICES, value="cmn", label="目標語言")
    audio_in = gr.Audio(sources=["microphone", "upload"], type="numpy", label="輸入音檔")
    want_speech = gr.Checkbox(label="同時合成目標語言語音", value=True)
    btn = gr.Button("翻譯", variant="primary")
    text_out = gr.Textbox(label="翻譯文字", lines=3)
    audio_out = gr.Audio(label="翻譯語音", type="filepath")
    btn.click(translate, inputs=[audio_in, src, tgt, want_speech], outputs=[text_out, audio_out])


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0")
