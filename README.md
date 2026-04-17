# 台語 ↔ 中文 語音翻譯（API 版）

透過 **Replicate 託管的 Meta [SeamlessM4T v2](https://replicate.com/cjwbw/seamless_communication)** 做台語（閩南語）↔ 中文雙向語音翻譯。**不用本機 GPU、不用下載 9GB 權重**，按秒計費（一次翻譯大約不到一美分）。

包含：

- **Gradio 網頁 demo**（`app.py`）
- **FastAPI 後端**（`server.py`）：把 API token 藏起來，給 App 呼叫的薄 proxy
- **Android App**（`android/`）：Kotlin + Jetpack Compose，錄音上傳後端、播放翻譯語音
- **GitHub Actions**：自動建 debug APK，在 Actions artifacts 下載

## 架構

```
┌──────────────┐  audio ┌────────────┐  audio  ┌───────────────────┐
│  Android App │ ─────▶ │  FastAPI   │ ──────▶ │  Replicate        │
│  (Compose)   │ ◀──── │  (proxy,   │ ◀────── │  SeamlessM4T v2   │
└──────────────┘  text │   API key) │   text  └───────────────────┘
                        └────────────┘
```

後端本身不載入模型、不需要 GPU，一台最小的 VM 就能跑。

## 準備

1. 到 [Replicate → API tokens](https://replicate.com/account/api-tokens) 拿一把 token（格式 `r8_...`）
2. 設環境變數：
   ```bash
   export REPLICATE_API_TOKEN=r8_xxx
   ```

## 後端 / 網頁 demo

```bash
pip install -r requirements.txt

# Gradio 網頁介面
python app.py          # http://localhost:7860

# FastAPI（給 Android App 連）
python server.py       # http://localhost:8000
# 健康檢查： curl http://localhost:8000/health
```

### API 端點

`POST /translate`  multipart/form-data

| 欄位 | 型態 | 說明 |
| --- | --- | --- |
| `audio` | file | WAV（16kHz 最佳；其他格式 Replicate 端會自行處理）|
| `src_lang` | str | `hok` 或 `cmn` |
| `tgt_lang` | str | `hok` 或 `cmn`（需與 src 不同）|
| `with_speech` | bool | 是否同時合成目標語言語音 |

回傳：`{"text": "...", "audio_b64": "<wav base64 or null>"}`

## Android App

位置：`android/`，套件名 `com.taigi.translator`，`minSdk 24`（Android 7.0+）。

### 取得 APK

- **自動建置**：push 後到 GitHub Actions → `Android APK` workflow → 下載 artifact `taigi-translator-debug-apk`
- **自己建**：
  ```bash
  cd android
  gradle wrapper --gradle-version 8.9
  ./gradlew :app:assembleDebug
  # 產出：android/app/build/outputs/apk/debug/app-debug.apk
  ```
  或用 Android Studio 直接開 `android/` 目錄。

### 使用方式

1. 電腦端 `python server.py` 起後端
2. App 頂部輸入後端網址
   - 模擬器：`http://10.0.2.2:8000`
   - 同 Wi-Fi 實機：`http://<電腦 IP>:8000`
3. 用箭頭按鈕切換方向（台語↔中文）
4. 按「開始錄音」→「停止並翻譯」

## 成本

Replicate 的 SeamlessM4T 跑在 T4 GPU，每秒約 $0.000725。一句幾秒鐘的翻譯通常 < $0.01。可在 Replicate 後台設硬上限。

## 替代方案

| 方案 | 優點 | 缺點 |
| --- | --- | --- |
| **Replicate**（本專案）| 一把 API key、雙向語音、閩南語支援好 | 按秒計費、需連網 |
| Google Cloud Translation + TTS | 穩定、文字品質好 | 閩南語 STT 官方支援不完整 |
| 本機跑 SeamlessM4T | 離線、免費 | 9GB 權重 + GPU |
| Whisper + NMT 拼裝 | 彈性 | 閩南語辨識率差 |

要切回本機版，把 `translator.py` 換成 transformers 版本即可，API 介面不變。

## 檔案一覽

```
translator.py                 Replicate 呼叫封裝（共用）
app.py                        Gradio 介面
server.py                     FastAPI proxy
requirements.txt
android/                      Android 專案（Gradle + Compose）
  app/src/main/
    AndroidManifest.xml
    java/com/taigi/translator/
      MainActivity.kt         UI（Compose）
      TranslateViewModel.kt   狀態機
      WavRecorder.kt          16kHz PCM → WAV
      TranslatorApi.kt        OkHttp 呼叫後端
    res/                      theme / strings / icon
.github/workflows/android.yml CI 自動建 APK
```
