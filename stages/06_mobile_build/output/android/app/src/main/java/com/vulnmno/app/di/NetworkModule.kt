package com.vulnmno.app.di

import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import com.vulnmno.app.BuildConfig
import com.vulnmno.app.data.remote.ApiService
import com.vulnmno.app.data.remote.AuthEventBus
import com.vulnmno.app.data.remote.AuthInterceptor
import com.vulnmno.app.data.remote.BaseUrlInterceptor
import com.vulnmno.app.data.remote.TokenAuthenticator
import com.vulnmno.app.data.local.TokenStore
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Provider
import javax.inject.Singleton
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import java.util.concurrent.TimeUnit

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides @Singleton
    fun json(): Json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        explicitNulls = false
    }

    @Provides @Singleton
    fun authBus(): AuthEventBus = AuthEventBus()

    @Provides @Singleton
    fun okHttp(
        baseUrlInterceptor: BaseUrlInterceptor,
        authInterceptor: AuthInterceptor,
        tokenAuthenticator: TokenAuthenticator,
    ): OkHttpClient {
        val log = HttpLoggingInterceptor().apply {
            level = if (BuildConfig.DEBUG) HttpLoggingInterceptor.Level.BASIC
            else HttpLoggingInterceptor.Level.NONE
        }
        return OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            // Order matters: rewrite the host first, then attach the bearer.
            .addInterceptor(baseUrlInterceptor)
            .addInterceptor(authInterceptor)
            .addInterceptor(log)
            .authenticator(tokenAuthenticator)
            .build()
    }

    @Provides @Singleton
    fun retrofit(json: Json, client: OkHttpClient): Retrofit {
        val contentType = "application/json".toMediaType()
        return Retrofit.Builder()
            .baseUrl(BuildConfig.BASE_URL)
            .client(client)
            .addConverterFactory(json.asConverterFactory(contentType))
            .build()
    }

    @Provides @Singleton
    fun api(retrofit: Retrofit): ApiService = retrofit.create(ApiService::class.java)

    @Provides @Singleton
    fun tokenAuthenticator(
        tokens: TokenStore,
        apiProvider: Provider<ApiService>,
        bus: AuthEventBus,
    ): TokenAuthenticator = TokenAuthenticator(tokens, apiProvider, bus)
}
