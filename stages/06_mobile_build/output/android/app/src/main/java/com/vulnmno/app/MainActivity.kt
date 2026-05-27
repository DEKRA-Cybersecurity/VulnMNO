package com.vulnmno.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.compose.rememberNavController
import com.vulnmno.app.ui.navigation.VulnMnoNavHost
import com.vulnmno.app.ui.navigation.AuthGate
import com.vulnmno.app.ui.theme.VulnMnoTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            VulnMnoTheme {
                val nav = rememberNavController()
                val gate: AuthGate = hiltViewModel()
                val authState by gate.state.collectAsState()
                VulnMnoNavHost(nav = nav, authState = authState, onAuthEvent = gate::onEvent)
            }
        }
    }
}
