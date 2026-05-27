package com.vulnmno.app.ui.navigation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.vulnmno.app.data.local.TokenStore
import com.vulnmno.app.data.remote.AuthEvent
import com.vulnmno.app.data.remote.AuthEventBus
import com.vulnmno.app.data.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed interface AuthState {
    data object Resolving : AuthState
    data object LoggedIn : AuthState
    data object LoggedOut : AuthState
}

sealed interface AuthIntent {
    data object Logout : AuthIntent
}

@HiltViewModel
class AuthGate @Inject constructor(
    private val tokens: TokenStore,
    private val authRepo: AuthRepository,
    bus: AuthEventBus,
) : ViewModel() {

    private val _state = MutableStateFlow<AuthState>(AuthState.Resolving)
    val state: StateFlow<AuthState> = _state.asStateFlow()

    init {
        // DataStore is the single source of truth for whether we have a session.
        // Subscribing reactively means every `AuthGate` instance — Activity-scoped,
        // NavBackStackEntry-scoped, whichever Hilt produced — converges on the same
        // state without any explicit `markLoggedIn` / `markLoggedOut` plumbing.
        viewModelScope.launch {
            // Bootstrap: if we landed with a refresh token but no access, try to swap
            // for a fresh access before exposing any state. This avoids a Login → Home
            // flicker for users with stored sessions.
            val (access, refresh) = tokens.read()
            if (access == null && refresh != null) {
                authRepo.restoreSession()  // success updates DataStore; failure leaves it empty
            }
            // Now follow DataStore for the lifetime of this ViewModel.
            tokens.accessTokenFlow.collect { token ->
                _state.value = if (token != null) AuthState.LoggedIn else AuthState.LoggedOut
            }
        }
        // External logouts (TokenAuthenticator after a failed refresh) — DataStore
        // gets cleared in that path too, so the collect above will also fire, but
        // this listener makes the transition immediate.
        viewModelScope.launch {
            bus.events.collect { ev ->
                if (ev is AuthEvent.LoggedOut) _state.value = AuthState.LoggedOut
            }
        }
    }

    fun onEvent(intent: AuthIntent) {
        when (intent) {
            is AuthIntent.Logout -> viewModelScope.launch {
                authRepo.logout()
                // tokens.clear() runs inside authRepo.logout()'s finally block, which
                // emits null on accessTokenFlow → state goes LoggedOut → LaunchedEffect
                // in NavHost navigates to LoginScreen.
            }
        }
    }

    /** Kept for call-site compatibility with LoginScreen. No-op since DataStore drives state. */
    fun markLoggedIn() {
        // intentionally left blank
    }
}
