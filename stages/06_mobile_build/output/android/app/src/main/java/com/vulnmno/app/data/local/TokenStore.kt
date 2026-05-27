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

private val Context.dataStore by preferencesDataStore(name = "vulnmno_auth")

@Singleton
class TokenStore @Inject constructor(@ApplicationContext private val ctx: Context) {
    private val access = stringPreferencesKey("access")
    private val refresh = stringPreferencesKey("refresh")
    private val msisdn = stringPreferencesKey("last_msisdn")

    val accessTokenFlow: Flow<String?> = ctx.dataStore.data.map { it[access] }
    val refreshTokenFlow: Flow<String?> = ctx.dataStore.data.map { it[refresh] }
    val lastMsisdnFlow: Flow<String?> = ctx.dataStore.data.map { it[msisdn] }

    suspend fun read(): Pair<String?, String?> {
        val prefs = ctx.dataStore.data.first()
        return prefs[access] to prefs[refresh]
    }

    suspend fun save(accessToken: String, refreshToken: String, msisdnValue: String? = null) {
        ctx.dataStore.edit {
            it[access] = accessToken
            it[refresh] = refreshToken
            if (msisdnValue != null) it[msisdn] = msisdnValue
        }
    }

    suspend fun clear() {
        ctx.dataStore.edit {
            it.remove(access); it.remove(refresh)
        }
    }
}
