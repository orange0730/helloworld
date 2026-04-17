package com.taigi.translator

import android.app.Application
import android.media.MediaPlayer
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File

enum class Lang(val code: String, val label: String) {
    HOK("hok", "台語"),
    CMN("cmn", "中文"),
}

data class UiState(
    val baseUrl: String = "http://10.0.2.2:8000",
    val src: Lang = Lang.HOK,
    val tgt: Lang = Lang.CMN,
    val isRecording: Boolean = false,
    val isTranslating: Boolean = false,
    val resultText: String = "",
    val error: String? = null,
    val canPlay: Boolean = false,
)

class TranslateViewModel(app: Application) : AndroidViewModel(app) {
    private val _state = MutableStateFlow(UiState())
    val state: StateFlow<UiState> = _state.asStateFlow()

    private val wavFile: File = File(app.cacheDir, "input.wav")
    private val replyFile: File = File(app.cacheDir, "reply.wav")
    private val recorder = WavRecorder(wavFile)
    private var player: MediaPlayer? = null

    fun setBaseUrl(url: String) = _state.update { it.copy(baseUrl = url) }

    fun swapLangs() = _state.update { it.copy(src = it.tgt, tgt = it.src, resultText = "", canPlay = false) }

    fun startRecording() {
        if (_state.value.isRecording) return
        recorder.start()
        _state.update { it.copy(isRecording = true, error = null) }
    }

    fun stopAndTranslate() {
        if (!_state.value.isRecording) return
        viewModelScope.launch {
            recorder.stop()
            _state.update { it.copy(isRecording = false, isTranslating = true, resultText = "", canPlay = false) }
            runCatching {
                withContext(Dispatchers.IO) {
                    val api = TranslatorApi(_state.value.baseUrl)
                    api.translate(wavFile, _state.value.src.code, _state.value.tgt.code, withSpeech = true)
                }
            }.onSuccess { r ->
                r.audioWav?.let { replyFile.writeBytes(it) }
                _state.update {
                    it.copy(
                        isTranslating = false,
                        resultText = r.text,
                        canPlay = r.audioWav != null,
                    )
                }
            }.onFailure { e ->
                _state.update { it.copy(isTranslating = false, error = e.message ?: "translation failed") }
            }
        }
    }

    fun play() {
        if (!_state.value.canPlay) return
        player?.release()
        player = MediaPlayer().apply {
            setDataSource(replyFile.absolutePath)
            setOnCompletionListener { release(); player = null }
            prepare()
            start()
        }
    }

    override fun onCleared() {
        player?.release()
        player = null
    }
}
