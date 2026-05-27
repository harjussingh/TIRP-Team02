package com.example.saca.util

import android.Manifest
import android.app.Activity
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

fun initiateEmergencyCall(context: Context) {
    // Check if CALL_PHONE permission is granted at runtime
    val hasPermission = ContextCompat.checkSelfPermission(
        context, Manifest.permission.CALL_PHONE
    ) == PackageManager.PERMISSION_GRANTED

    if (hasPermission) {
        // Permission granted — make the call directly
        try {
            val intent = Intent(Intent.ACTION_CALL).apply {
                data = Uri.parse("tel:000")
            }
            context.startActivity(intent)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    } else {
        // Permission not granted — request it
        // Falls back to dial screen so user can call manually
        try {
            val intent = Intent(Intent.ACTION_DIAL).apply {
                data = Uri.parse("tel:000")
            }
            context.startActivity(intent)
        } catch (e: Exception) {
            e.printStackTrace()
        }

        // Also request permission for next time
        if (context is Activity) {
            ActivityCompat.requestPermissions(
                context,
                arrayOf(Manifest.permission.CALL_PHONE),
                1001
            )
        }
    }
}