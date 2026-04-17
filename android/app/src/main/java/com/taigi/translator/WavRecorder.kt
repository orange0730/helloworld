package com.taigi.translator

import android.Manifest
import android.annotation.SuppressLint
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import androidx.annotation.RequiresPermission
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.concurrent.thread

/**
 * 錄 16kHz / 16-bit / mono PCM 並包成 WAV，避開手機端格式轉換問題。
 * SeamlessM4T 預期 16kHz；直接錄就給它要的格式最省事。
 */
class WavRecorder(private val outFile: File) {
    private val sampleRate = 16_000
    private val channelConfig = AudioFormat.CHANNEL_IN_MONO
    private val encoding = AudioFormat.ENCODING_PCM_16BIT

    @Volatile private var recording = false
    private var thread: Thread? = null
    private var record: AudioRecord? = null

    val isRecording: Boolean get() = recording

    @SuppressLint("MissingPermission")
    @RequiresPermission(Manifest.permission.RECORD_AUDIO)
    fun start() {
        if (recording) return
        val bufSize = AudioRecord.getMinBufferSize(sampleRate, channelConfig, encoding)
            .coerceAtLeast(4096)

        val ar = AudioRecord(
            MediaRecorder.AudioSource.MIC,
            sampleRate,
            channelConfig,
            encoding,
            bufSize,
        )
        record = ar
        ar.startRecording()
        recording = true

        val pcmFile = File(outFile.parentFile, outFile.nameWithoutExtension + ".pcm")
        thread = thread(start = true, name = "WavRecorder") {
            FileOutputStream(pcmFile).use { fos ->
                val buffer = ByteArray(bufSize)
                while (recording) {
                    val n = ar.read(buffer, 0, buffer.size)
                    if (n > 0) fos.write(buffer, 0, n)
                }
            }
            writeWav(pcmFile, outFile, sampleRate, 1, 16)
            pcmFile.delete()
        }
    }

    suspend fun stop(): File = withContext(Dispatchers.IO) {
        if (!recording) return@withContext outFile
        recording = false
        record?.stop()
        record?.release()
        record = null
        thread?.join()
        thread = null
        outFile
    }

    private fun writeWav(pcm: File, wav: File, sampleRate: Int, channels: Int, bits: Int) {
        val pcmBytes = pcm.readBytes()
        val byteRate = sampleRate * channels * bits / 8
        FileOutputStream(wav).use { out ->
            val header = ByteBuffer.allocate(44).order(ByteOrder.LITTLE_ENDIAN).apply {
                put("RIFF".toByteArray())
                putInt(36 + pcmBytes.size)
                put("WAVE".toByteArray())
                put("fmt ".toByteArray())
                putInt(16)
                putShort(1.toShort())
                putShort(channels.toShort())
                putInt(sampleRate)
                putInt(byteRate)
                putShort((channels * bits / 8).toShort())
                putShort(bits.toShort())
                put("data".toByteArray())
                putInt(pcmBytes.size)
            }.array()
            out.write(header)
            out.write(pcmBytes)
        }
    }
}
