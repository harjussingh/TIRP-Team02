package com.example.saca

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.rememberNavController
import com.example.saca.navigation.AppNavGraph
import com.example.saca.ui.components.EmergencyCallButton
import com.example.saca.ui.theme.SacaTheme
import com.example.saca.util.initiateEmergencyCall
import com.example.saca.viewmodel.TriageViewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            SacaTheme {
                val navController = rememberNavController()
                val viewModel: TriageViewModel = viewModel()
                
                Scaffold(
                    floatingActionButton = {
                        EmergencyCallButton(
                            viewModel = viewModel,
                            onEmergencyCallConfirmed = {
                                initiateEmergencyCall(this@MainActivity)
                            },
                            modifier = Modifier.padding(bottom = 80.dp)
                        )
                    }
                ) {
                    AppNavGraph(navController = navController, viewModel = viewModel)
                }
            }
        }
    }
}