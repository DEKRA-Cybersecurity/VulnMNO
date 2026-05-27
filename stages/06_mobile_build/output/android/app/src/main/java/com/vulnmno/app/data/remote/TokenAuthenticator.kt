package com.vulnmno.app.data.remote

import com.vulnmno.app.data.local.TokenStore
import com.vulnmno.app.data.remote.dto.RefreshRequestDto
import javax.inject.Inject
import javax.inject.Provider
import kotlinx.coroutines.channels.BufferOverflow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.runBlocking
import okhttp3.Authenticator
import okhttp3.Request
import okhttp3.Response
import okhttp3.Route

class TokenAuthenticator @Inject constructor(
    private val tokens: TokenStore,
    private val apiProvider: Provider<ApiService>,
    val authEvents: AuthEventBus,
) : Authenticator {

    override fun authenticate(route: Route?, response: Response): Request? {
        if (response.request.header("Authorization") == null) return null
        if (responseCount(response) >= 2) {
            runBlocking { tokens.clear(); authEvents.emitLoggedOut() }
            return null
        }
        val refresh = runBlocking { tokens.read().second } ?: return null
        return try {
            val pair = runBlocking { apiProvider.get().refresh(RefreshRequestDto(refresh)) }
            runBlocking { tokens.save(pair.accessToken, pair.refreshToken) }
            response.request.newBuilder()
                .header("Authorization", "Bearer ${pair.accessToken}")
                .build()
        } catch (_: Throwable) {
            runBlocking { tokens.clear(); authEvents.emitLoggedOut() }
            null
        }
    }

    private fun responseCount(response: Response): Int {
        var c = 1
        var prior = response.priorResponse
        while (prior != null) { c++; prior = prior.priorResponse }
        return c
    }
}

class AuthEventBus @Inject constructor() {
    private val _events = MutableSharedFlow<AuthEvent>(
        extraBufferCapacity = 16, onBufferOverflow = BufferOverflow.DROP_OLDEST,
    )
    val events = _events.asSharedFlow()
    suspend fun emitLoggedOut() { _events.emit(AuthEvent.LoggedOut) }
}

sealed interface AuthEvent {
    data object LoggedOut : AuthEvent
}
