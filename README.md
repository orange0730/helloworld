# 台語 ↔ 中文 語音翻譯

以 Meta [SeamlessM4T v2](https://huggingface.co/facebook/seamless-m4t-v2-large) 為核心的**雙向**台語（閩南語）/ 中文語音翻譯系統，含：

- **Gradio 網頁 demo**（`app.py`）
- **FastAPI 後端**（`server.py`）：提供 `/translate` API
- **Android App**（`android/`）：Kotlin + Jetpack Compose，錄音上傳後端、播放翻譯語音
- **GitHub Actions**：自動建 debug APK，Actions artifacts 可直接下載

## 架構

```
┌──────────────┐   audio (wav)   ┌───────────────────────────┐
│  Android App │ ───────────────▶│  FastAPI + SeamlessM4T v2 │
│  (Compose)   │ ◀─ text + wav ──│      hok ↔ cmn            │
└──────────────┘                 └───────────────────────────┘
```

單一模型同時完成語音辨識、翻譯、語音合成，方向只差在 `src_lang` / `tgt_lang`。

## 後端

```bash
pip install -r requirements.txt

# 方式 A：Gradio 網頁介面
python app.py          # http://localhost:7860

# 方式 B：FastAPI（給 Android App 連）
python server.py       # http://localhost:8000
# 健康檢查： curl http://localhost:8000/health
```

需求：Python 3.10+，建議 GPU（VRAM ≥ 10GB）；首次下載權重約 9GB。

### API 端點

`POST /translate`  multipart/form-data

| 欄位 | 型態 | 說明 |
| --- | --- | --- |
| `audio` | file | 16-bit WAV，建議 16kHz 單聲道 |
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

1. 在 App 頂部輸入後端網址
   - 模擬器：`http://10.0.2.2:8000`
   - 同 Wi-Fi 實機：`http://<電腦 IP>:8000`
2. 用中間箭頭按鈕切換方向（台語↔中文）
3. 按「開始錄音」→ 按「停止並翻譯」
4. 顯示翻譯文字 + 可播放合成語音

### 功能

- 16kHz PCM 原生錄音（避免手機編碼差異）
- 雙向切換 `hok ↔ cmn`
- 文字 + 語音雙輸出
- 後端網址可於 UI 內修改（方便公測期直接換 server）

## 檔案一覽

```
app.py                        Gradio 介面
server.py                     FastAPI 後端
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

## 已知限制 / 下一步

- SeamlessM4T 權重 9GB，無法放進 APK，**一定要有後端**
- 要離線 / on-device：可改用 Whisper small + 小型 NMT，但閩南語辨識率會掉
- 要全託管：改走 Google Cloud Translation API（已支援台語文字，語音需接 TTS）
- 特定領域口音：準備平行語料後對模型 fine-tune
- TLS / 驗證 / 使用者額度等，視部署情境再加
