package com.example.voicecamera

import android.Manifest
import android.content.ContentValues
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.provider.MediaStore
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.util.Log
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.example.voicecamera.databinding.ActivityMainBinding
import java.text.SimpleDateFormat
import java.util.Locale
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var cameraExecutor: ExecutorService
    private lateinit var speechRecognizer: SpeechRecognizer

    private var imageCapture: ImageCapture? = null
    private var isListening = false

    companion object {
        private const val TAG = "VoiceCamera"
        private const val REQUEST_CODE_PERMISSIONS = 10
        private val REQUIRED_PERMISSIONS = mutableListOf(
            Manifest.permission.CAMERA,
            Manifest.permission.RECORD_AUDIO
        ).apply {
            if (Build.VERSION.SDK_INT <= Build.VERSION_CODES.P) {
                add(Manifest.permission.WRITE_EXTERNAL_STORAGE)
            }
        }.toTypedArray()

        // Keywords that trigger the shutter (case-insensitive, supports variants)
        private val TRIGGER_KEYWORDS = listOf("拍照", "拍一張", "拍照片", "照相")
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        if (allPermissionsGranted()) {
            startCamera()
            setupSpeechRecognizer()
            startListening()
        } else {
            ActivityCompat.requestPermissions(this, REQUIRED_PERMISSIONS, REQUEST_CODE_PERMISSIONS)
        }

        binding.btnShutter.setOnClickListener { takePhoto() }

        cameraExecutor = Executors.newSingleThreadExecutor()
    }

    // ── Camera ────────────────────────────────────────────────────────────────

    private fun startCamera() {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(this)
        cameraProviderFuture.addListener({
            val cameraProvider = cameraProviderFuture.get()

            val preview = Preview.Builder().build().also {
                it.setSurfaceProvider(binding.viewFinder.surfaceProvider)
            }

            imageCapture = ImageCapture.Builder()
                .setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY)
                .build()

            try {
                cameraProvider.unbindAll()
                cameraProvider.bindToLifecycle(
                    this,
                    CameraSelector.DEFAULT_BACK_CAMERA,
                    preview,
                    imageCapture
                )
            } catch (e: Exception) {
                Log.e(TAG, "Camera bind failed", e)
            }
        }, ContextCompat.getMainExecutor(this))
    }

    private fun takePhoto() {
        val imageCapture = imageCapture ?: return

        // Flash animation
        binding.flashOverlay.visibility = View.VISIBLE
        binding.flashOverlay.animate().alpha(0f).setDuration(300).withEndAction {
            binding.flashOverlay.visibility = View.GONE
            binding.flashOverlay.alpha = 1f
        }.start()

        val name = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(System.currentTimeMillis())
        val contentValues = ContentValues().apply {
            put(MediaStore.MediaColumns.DISPLAY_NAME, "IMG_$name")
            put(MediaStore.MediaColumns.MIME_TYPE, "image/jpeg")
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                put(MediaStore.Images.Media.RELATIVE_PATH, "Pictures/VoiceCamera")
            }
        }

        val outputOptions = ImageCapture.OutputFileOptions.Builder(
            contentResolver,
            MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
            contentValues
        ).build()

        imageCapture.takePicture(
            outputOptions,
            ContextCompat.getMainExecutor(this),
            object : ImageCapture.OnImageSavedCallback {
                override fun onImageSaved(output: ImageCapture.OutputFileResults) {
                    val msg = "已儲存：Pictures/VoiceCamera/IMG_$name"
                    showStatus(msg)
                    Log.d(TAG, msg)
                }

                override fun onError(e: ImageCaptureException) {
                    Log.e(TAG, "拍照失敗", e)
                    showStatus("拍照失敗：${e.message}")
                }
            }
        )
    }

    // ── Speech Recognition ────────────────────────────────────────────────────

    private fun setupSpeechRecognizer() {
        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            showStatus("此裝置不支援語音辨識")
            return
        }

        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this)
        speechRecognizer.setRecognitionListener(object : RecognitionListener {

            override fun onResults(results: Bundle) {
                val matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                if (matches != null) {
                    handleSpeechResult(matches)
                }
                // Restart listening immediately after each result
                if (isListening) restartListening()
            }

            override fun onPartialResults(partialResults: Bundle) {
                val partial = partialResults.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                if (!partial.isNullOrEmpty()) {
                    val text = partial[0]
                    binding.tvRecognized.text = text
                    // Trigger on partial result for faster response
                    if (TRIGGER_KEYWORDS.any { text.contains(it) }) {
                        takePhoto()
                    }
                }
            }

            override fun onError(error: Int) {
                // Silently restart on common non-fatal errors
                val fatal = error == SpeechRecognizer.ERROR_RECOGNIZER_BUSY ||
                        error == SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS
                if (!fatal && isListening) {
                    restartListening()
                } else if (fatal) {
                    showStatus("語音辨識錯誤：$error")
                    isListening = false
                    updateListeningUI(false)
                }
            }

            override fun onEndOfSpeech() {}
            override fun onReadyForSpeech(params: Bundle) {
                showStatus("聆聽中…說「拍照」即可拍照")
            }
            override fun onBeginningOfSpeech() {}
            override fun onRmsChanged(rmsdB: Float) {
                // Animate mic icon opacity based on volume
                val alpha = (0.4f + (rmsdB.coerceIn(0f, 10f) / 10f) * 0.6f)
                binding.ivMic.alpha = alpha
            }
            override fun onBufferReceived(buffer: ByteArray?) {}
            override fun onEvent(eventType: Int, params: Bundle?) {}
        })
    }

    private fun handleSpeechResult(matches: List<String>) {
        val recognized = matches.firstOrNull() ?: return
        binding.tvRecognized.text = recognized
        if (TRIGGER_KEYWORDS.any { recognized.contains(it) }) {
            takePhoto()
        }
    }

    private fun startListening() {
        if (!::speechRecognizer.isInitialized) return
        isListening = true
        updateListeningUI(true)

        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, "zh-TW")
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, "zh-TW")
            putExtra(RecognizerIntent.EXTRA_ONLY_RETURN_LANGUAGE_MODEL_RESULTS, false)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            // Keep listening until silence
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, 1500L)
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS, 1500L)
        }
        speechRecognizer.startListening(intent)
    }

    private fun restartListening() {
        speechRecognizer.stopListening()
        // Small delay to let the recognizer reset
        binding.root.postDelayed({ startListening() }, 300)
    }

    private fun stopListening() {
        isListening = false
        speechRecognizer.stopListening()
        updateListeningUI(false)
    }

    // ── UI helpers ────────────────────────────────────────────────────────────

    private fun updateListeningUI(listening: Boolean) {
        binding.ivMic.setImageResource(
            if (listening) R.drawable.ic_mic_on else R.drawable.ic_mic_off
        )
        binding.tvStatus.text = if (listening) "聆聽中…說「拍照」即可拍照" else "已停止聆聽"
    }

    private fun showStatus(msg: String) {
        runOnUiThread {
            binding.tvStatus.text = msg
            Toast.makeText(this, msg, Toast.LENGTH_SHORT).show()
        }
    }

    // ── Permissions ───────────────────────────────────────────────────────────

    override fun onRequestPermissionsResult(
        requestCode: Int, permissions: Array<String>, grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQUEST_CODE_PERMISSIONS) {
            if (allPermissionsGranted()) {
                startCamera()
                setupSpeechRecognizer()
                startListening()
            } else {
                showStatus("需要相機與麥克風權限才能使用此 APP")
            }
        }
    }

    private fun allPermissionsGranted() = REQUIRED_PERMISSIONS.all {
        ContextCompat.checkSelfPermission(baseContext, it) == PackageManager.PERMISSION_GRANTED
    }

    // ── Lifecycle ─────────────────────────────────────────────────────────────

    override fun onResume() {
        super.onResume()
        if (allPermissionsGranted() && !isListening) {
            setupSpeechRecognizer()
            startListening()
        }
    }

    override fun onPause() {
        super.onPause()
        stopListening()
    }

    override fun onDestroy() {
        super.onDestroy()
        if (::speechRecognizer.isInitialized) speechRecognizer.destroy()
        cameraExecutor.shutdown()
    }
}
