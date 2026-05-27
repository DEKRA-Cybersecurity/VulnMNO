package com.vulnmno.app.data.remote

import com.vulnmno.app.data.remote.dto.ErrorEnvelope
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonPrimitive
import retrofit2.HttpException

/** Sealed result mapping HttpException / IOException onto a structured error. */
sealed interface AppError {
    val message: String
    data class Network(override val message: String = "Network error") : AppError
    data class Domain(val code: String, override val message: String, val rule: String? = null, val raw: ErrorEnvelope) : AppError
    data class Unknown(override val message: String) : AppError
}

private val json = Json { ignoreUnknownKeys = true; isLenient = true }

fun Throwable.toAppError(): AppError = when (this) {
    is HttpException -> {
        val body = response()?.errorBody()?.string()
        try {
            val env = body?.let { json.decodeFromString(ErrorEnvelope.serializer(), it) }
            if (env != null) {
                val rule = env.error.details?.get("rule")?.jsonPrimitive?.contentOrNull
                AppError.Domain(env.error.code, env.error.message, rule, env)
            } else {
                AppError.Unknown("HTTP ${code()}")
            }
        } catch (_: Throwable) {
            AppError.Unknown("HTTP ${code()}")
        }
    }
    is java.io.IOException -> AppError.Network(message ?: "Network error")
    else -> AppError.Unknown(message ?: "Unknown error")
}

private val kotlinx.serialization.json.JsonPrimitive.contentOrNull: String?
    get() = try { content } catch (_: Throwable) { null }
