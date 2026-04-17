package com.taigi.translator

import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.File
import java.util.concurrent.TimeUnit

data class TranslationResult(val text: String, val audioWav: ByteArray?)

class TranslatorApi(private val baseUrl: String) {
    private val client = OkHttpClient.Builder()
        .callTimeout(120, TimeUnit.SECONDS)
        .readTimeout(120, TimeUnit.SECONDS)
        .build()

    fun translate(
        wav: File,
        srcLang: String,
        tgtLang: String,
        withSpeech: Boolean,
    ): TranslationResult {
        val body = MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart("audio", wav.name, wav.asRequestBody("audio/wav".toMediaType()))
            .addFormDataPart("src_lang", srcLang)
            .addFormDataPart("tgt_lang", tgtLang)
            .addFormDataPart("with_speech", withSpeech.toString())
            .build()

        val url = baseUrl.trimEnd('/') + "/translate"
        val request = Request.Builder().url(url).post(body).build()
        client.newCall(request).execute().use { resp ->
            val raw = resp.body?.string().orEmpty()
            if (!resp.isSuccessful) error("HTTP ${resp.code}: $raw")
            val json = JSONObject(raw)
            val text = json.optString("text")
            val b64 = json.optString("audio_b64").takeIf { it.isNotEmpty() && it != "null" }
            val audio = b64?.let { android.util.Base64.decode(it, android.util.Base64.DEFAULT) }
            return TranslationResult(text, audio)
        }
    }
}
