package com.vulnmno.app.data.remote

import com.vulnmno.app.data.local.BaseUrlStore
import javax.inject.Inject
import kotlinx.coroutines.runBlocking
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull
import okhttp3.Interceptor
import okhttp3.Response

/**
 * Reroutes every outgoing request to a user-supplied backend when
 * [BaseUrlStore] holds an override; otherwise lets requests pass through
 * unchanged (which keeps the compile-time `BuildConfig.BASE_URL` in effect —
 * `https://10.0.2.2/` since stage 16).
 *
 * Override input → resolved URL truth table:
 *
 *   - `192.168.1.42`           → `https://192.168.1.42:443`
 *       Default for bare hosts. Goes through the Caddy reverse-proxy.
 *   - `192.168.1.42:443`       → `https://192.168.1.42:443`
 *       Explicit HTTPS port.
 *   - `192.168.1.42:8000`      → `http://192.168.1.42:8000`
 *       Explicit `:8000` is interpreted as "bypass Caddy and hit the
 *       backend directly over plain HTTP". Preserves the M1/M3 downgrade
 *       lab (training surface — see docs/vulns/mobile/).
 *   - `http://host[:port]`     → as typed.
 *   - `https://host[:port]`    → as typed.
 *
 * Must run before [AuthInterceptor] so the bearer is added to the
 * rewritten request.
 */
class BaseUrlInterceptor @Inject constructor(private val store: BaseUrlStore) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val req = chain.request()
        val override = runBlocking { store.current() }?.takeIf { it.isNotBlank() } ?: return chain.proceed(req)
        val target = normalize(override) ?: return chain.proceed(req)
        val newUrl = req.url.newBuilder()
            .scheme(target.scheme)
            .host(target.host)
            .port(target.port)
            .build()
        return chain.proceed(req.newBuilder().url(newUrl).build())
    }

    private fun normalize(raw: String): okhttp3.HttpUrl? {
        val trimmed = raw.trim().removeSuffix("/")
        if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
            return trimmed.toHttpUrlOrNull()
        }
        val afterScheme = trimmed
        val hadExplicitPort = afterScheme.contains(":")
        // Default to HTTPS via Caddy when no port is given. If the user
        // explicitly typed `:8000`, treat as plain HTTP (the backend's
        // direct port). Any other explicit port stays HTTPS.
        val explicitPort = if (hadExplicitPort) afterScheme.substringAfter(":").toIntOrNull() else null
        val scheme = if (explicitPort == 8000) "http" else "https"
        val effectivePort = explicitPort ?: 443
        val host = if (hadExplicitPort) afterScheme.substringBefore(":") else afterScheme
        return "$scheme://$host:$effectivePort".toHttpUrlOrNull()
    }
}
