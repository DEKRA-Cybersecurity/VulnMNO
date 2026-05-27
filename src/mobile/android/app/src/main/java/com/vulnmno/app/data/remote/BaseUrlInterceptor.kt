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
 * unchanged (which keeps the compile-time `BuildConfig.BASE_URL` in effect).
 *
 * Accepts three input shapes for the override:
 *   - `192.168.1.42`                → `http://192.168.1.42:8000`
 *   - `192.168.1.42:8000`           → `http://192.168.1.42:8000`
 *   - `http(s)://host[:port][/...]` → used as-is
 *
 * Must run before [AuthInterceptor] so the bearer is added to the rewritten
 * request (same effect either way, but logically the rewrite happens first).
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
        val withScheme = if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) trimmed
        else "http://$trimmed"
        val parsed = withScheme.toHttpUrlOrNull() ?: return null
        // If the user typed just "192.168.1.42" without a port, default to 8000
        // (the port docker-compose publishes). HttpUrl's defaultPort() would
        // give 80, which is almost never what they meant in this context.
        val hadExplicitPort = withScheme.substringAfter("://").contains(":")
        return if (hadExplicitPort) parsed
        else parsed.newBuilder().port(8000).build()
    }
}
