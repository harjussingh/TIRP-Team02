package com.example.saca.util

import android.content.Context
import android.content.Intent
import android.net.Uri

fun initiateEmergencyCall(context: Context) {
    try {
        val intent = Intent(Intent.ACTION_CALL).apply {
            data = Uri.parse("tel:000")
        }
        context.startActivity(intent)
    } catch (e: SecurityException) {
        // CALL_PHONE permission not granted
        e.printStackTrace()
    } catch (e: Exception) {
        // Handle other exceptions (e.g., no dialer app available)
        e.printStackTrace()
    }
}
