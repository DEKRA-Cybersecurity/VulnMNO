package com.vulnmno.app.data.remote

import com.vulnmno.app.data.local.TokenStore
import javax.inject.Inject
import kotlinx.coroutines.runBlocking
import okhttp3.Interceptor
import okhttp3.Response

class AuthInterceptor @Inject constructor(private val tokens: TokenStore) : Interceptor {

    // Endpoints under /api/auth/ that are intentionally unauthenticated (no bearer needed).
    // Every other path — including /api/auth/logout, which the backend requires authenticated —
    // must carry the bearer token if one is available.
    private val unauthenticatedPaths = setOf(
        "/api/auth/login",
        "/api/auth/refresh",
        "/api/auth/otp/verify",
        "/api/auth/password-reset/request",
        "/api/auth/password-reset/confirm",
    )

    override fun intercept(chain: Interceptor.Chain): Response {
        val req = chain.request()
        if (req.url.encodedPath in unauthenticatedPaths) return chain.proceed(req)
        val access = runBlocking { tokens.read().first }
        val newReq = if (access.isNullOrBlank()) req
        else req.newBuilder().header("Authorization", "Bearer $access").build()
        return chain.proceed(newReq)
    }
}
