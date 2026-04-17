package com.taigi.translator

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material.icons.filled.SwapHoriz
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.lifecycle.viewmodel.compose.viewModel
import android.widget.Toast

class MainActivity : ComponentActivity() {

    private val viewModel: TranslateViewModel by viewModels()

    private val micPermission = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) viewModel.startRecording()
        else Toast.makeText(this, "請允許錄音權限", Toast.LENGTH_SHORT).show()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface(color = MaterialTheme.colorScheme.background) {
                    AppScreen(
                        vm = viewModel,
                        onMicClick = {
                            val granted = ContextCompat.checkSelfPermission(
                                this, Manifest.permission.RECORD_AUDIO
                            ) == PackageManager.PERMISSION_GRANTED
                            if (granted) viewModel.startRecording()
                            else micPermission.launch(Manifest.permission.RECORD_AUDIO)
                        }
                    )
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun AppScreen(
    vm: TranslateViewModel = viewModel(),
    onMicClick: () -> Unit,
) {
    val state by vm.state.collectAsState()
    val ctx = LocalContext.current

    Scaffold(topBar = { TopAppBar(title = { Text("台中翻譯  Taigi ↔ 中文") }) }) { pad ->
        Column(
            modifier = Modifier
                .padding(pad)
                .padding(16.dp)
                .fillMaxSize()
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            OutlinedTextField(
                value = state.baseUrl,
                onValueChange = vm::setBaseUrl,
                label = { Text("後端網址") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )

            Row(verticalAlignment = Alignment.CenterVertically) {
                LangBadge(state.src.label, Modifier.weight(1f))
                IconButton(onClick = vm::swapLangs) {
                    Icon(Icons.Default.SwapHoriz, contentDescription = "swap")
                }
                LangBadge(state.tgt.label, Modifier.weight(1f))
            }

            Spacer(Modifier.height(8.dp))

            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(140.dp),
                contentAlignment = Alignment.Center
            ) {
                when {
                    state.isTranslating -> CircularProgressIndicator()
                    state.isRecording -> Button(onClick = vm::stopAndTranslate) {
                        Icon(Icons.Default.Stop, contentDescription = null)
                        Spacer(Modifier.height(0.dp))
                        Text("  停止並翻譯")
                    }
                    else -> Button(onClick = onMicClick) {
                        Icon(Icons.Default.Mic, contentDescription = null)
                        Text("  開始錄音")
                    }
                }
            }

            Text("翻譯結果", fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
            Surface(
                tonalElevation = 2.dp,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(140.dp)
            ) {
                Text(
                    text = state.resultText.ifEmpty { "（錄音後顯示）" },
                    modifier = Modifier.padding(12.dp),
                    color = if (state.resultText.isEmpty()) Color.Gray else Color.Unspecified,
                )
            }

            Button(
                onClick = vm::play,
                enabled = state.canPlay,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Icon(Icons.Default.PlayArrow, contentDescription = null)
                Text("  播放翻譯語音")
            }

            state.error?.let {
                Text("錯誤：$it", color = MaterialTheme.colorScheme.error)
            }
        }
    }
}

@Composable
private fun LangBadge(label: String, modifier: Modifier = Modifier) {
    Surface(
        tonalElevation = 4.dp,
        modifier = modifier,
    ) {
        Text(
            text = label,
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 14.dp),
            fontSize = 18.sp,
            fontWeight = FontWeight.Bold,
            textAlign = androidx.compose.ui.text.style.TextAlign.Center,
        )
    }
}
