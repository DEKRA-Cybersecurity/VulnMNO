package com.vulnmno.app.data.local

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

private val Context.baseUrlDataStore by preferencesDataStore(name = "vulnmno_base_url")

/**
 * User-supplied override for the API base URL. When set, [BaseUrlInterceptor]
 * rewrites every outgoing request to point at this host instead of the
 * compile-time [com.vulnmno.app.BuildConfig.BASE_URL]. Used by the
 * "Physical device?" affordance on the login screen so the same APK works on
 * an emulator (default) and on a phone on the same Wi-Fi (override).
 */
@Singleton
class BaseUrlStore @Inject constructor(@ApplicationContext private val ctx: Context) {
    private val key = stringPreferencesKey("override_base_url")

    val overrideFlow: Flow<String?> = ctx.baseUrlDataStore.data.map { it[key] }

    suspend fun current(): String? = ctx.baseUrlDataStore.data.first()[key]

    suspend fun set(url: String) {
        ctx.baseUrlDataStore.edit { it[key] = url }
    }

    suspend fun clear() {
        ctx.baseUrlDataStore.edit { it.remove(key) }
    }
}
