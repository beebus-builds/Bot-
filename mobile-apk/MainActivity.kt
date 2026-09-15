package com.powerbot.controller

import android.os.Bundle
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.EditText
import android.widget.LinearLayout
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity

// Simple WebView wrapper for PowerBot.
// 1. Open in Android Studio -> Build -> Build APK
// 2. Install APK on phone (same Wi-Fi as laptop)
// 3. Enter laptop URL e.g. http://192.168.1.5:8080
class MainActivity : AppCompatActivity() {
    private lateinit var webView: WebView
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        webView = WebView(this)
        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true
        webView.webViewClient = WebViewClient()
        setContentView(webView)
        askUrl()
    }
    private fun askUrl() {
        val input = EditText(this)
        input.hint = "http://192.168.1.5:8080"
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(50, 40, 50, 10)
            addView(input)
        }
        AlertDialog.Builder(this)
            .setTitle("PowerBot - Laptop IP")
            .setMessage("Enter your laptop PowerBot URL (shown in desktop app)")
            .setView(layout)
            .setPositiveButton("Connect") { _, _ ->
                var url = input.text.toString().trim()
                if (url.isEmpty()) url = "http://192.168.1.5:8080"
                if (!url.startsWith("http")) url = "http://$url"
                webView.loadUrl(url)
            }
            .setCancelable(false)
            .show()
    }
    override fun onBackPressed() {
        if (::webView.isInitialized && webView.canGoBack()) webView.goBack()
        else super.onBackPressed()
    }
}
