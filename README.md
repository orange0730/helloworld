# 台語（閩南語）→ 中文 語音翻譯 Demo

以 Meta [SeamlessM4T v2](https://huggingface.co/facebook/seamless-m4t-v2-large) 打造的最小可跑範例。錄一段台語（Hokkien），輸出中文文字 + 中文合成語音。

## 架構

```
麥克風 / 音檔 ──► SeamlessM4T v2 (S2TT + S2ST) ──► 中文文字 + 中文語音
                          src_lang=hok, tgt_lang=cmn
```

單一模型同時完成：語音辨識、翻譯、語音合成。

## 系統需求

- Python 3.10+
- 建議 NVIDIA GPU（VRAM ≥ 10GB）；CPU 可跑但每句要等數十秒
- 首次啟動會下載模型權重約 9GB

## 安裝

```bash
pip install -r requirements.txt
```

## 執行

```bash
python app.py
```

瀏覽器開啟 http://localhost:7860 ，按麥克風錄音 → 點「翻譯」。

## 下一步可做的事

- 用小模型：`facebook/seamless-m4t-medium`（~1.2GB，效果略遜）
- 改走 API：Google Cloud Translation v3 已支援「台灣閩南語」
- 加入台羅拼音輸出：接教育部台灣閩南語常用詞辭典 API
- 特定領域 fine-tune：用自己的平行語料（台語音檔 + 中文逐字稿）繼續訓練

## 語言代碼（SeamlessM4T）

| 代碼 | 語言 |
| --- | --- |
| `hok` | 閩南語 / 台語（Hokkien） |
| `cmn` | 中文普通話（Mandarin） |
| `yue` | 粵語 |
| `eng` | 英文 |
