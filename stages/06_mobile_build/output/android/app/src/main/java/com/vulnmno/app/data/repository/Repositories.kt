package com.vulnmno.app.data.repository

import com.vulnmno.app.data.local.TokenStore
import com.vulnmno.app.data.remote.ApiService
import com.vulnmno.app.data.remote.AppError
import com.vulnmno.app.data.remote.dto.*
import com.vulnmno.app.data.remote.toAppError
import java.math.BigDecimal
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonPrimitive
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody

/** Tiny Result wrapper used by repositories. UI layer renders Ok/Err. */
sealed interface ApiResult<out T> {
    data class Ok<T>(val value: T) : ApiResult<T>
    data class Err(val error: AppError) : ApiResult<Nothing>
}

inline fun <T> runCatchingApi(block: () -> T): ApiResult<T> =
    try { ApiResult.Ok(block()) } catch (t: Throwable) { ApiResult.Err(t.toAppError()) }

private val json = Json { ignoreUnknownKeys = true; isLenient = true }

@Singleton
class AuthRepository @Inject constructor(
    private val api: ApiService,
    private val tokens: TokenStore,
) {
    sealed interface LoginOutcome {
        data class Tokens(val tokens: TokenPairDto) : LoginOutcome
        data class Otp(val challenge: OtpChallengeDto) : LoginOutcome
    }

    suspend fun login(msisdn: String, password: String): ApiResult<LoginOutcome> = runCatchingApi {
        val r = api.login(LoginRequestDto(msisdn, password))
        if (!r.isSuccessful) throw retrofit2.HttpException(r)
        val body = r.body() ?: error("Empty login body")
        val obj = body.toString()
        val map = json.parseToJsonElement(obj)
        val keys = (map as kotlinx.serialization.json.JsonObject).keys
        if ("accessToken" in keys) {
            val pair = json.decodeFromString(TokenPairDto.serializer(), obj)
            tokens.save(pair.accessToken, pair.refreshToken, msisdn)
            LoginOutcome.Tokens(pair)
        } else {
            val ch = json.decodeFromString(OtpChallengeDto.serializer(), obj)
            LoginOutcome.Otp(ch)
        }
    }

    suspend fun verifyOtp(token: String, code: String): ApiResult<TokenPairDto> = runCatchingApi {
        val pair = api.verifyOtp(OtpVerifyRequestDto(token, code))
        tokens.save(pair.accessToken, pair.refreshToken)
        pair
    }

    suspend fun logout(): ApiResult<Unit> = runCatchingApi {
        try { api.logout() } finally { tokens.clear() }
    }

    suspend fun requestPasswordReset(msisdn: String): ApiResult<Unit> = runCatchingApi {
        api.requestPasswordReset(PasswordResetRequestDto(msisdn))
        Unit
    }

    suspend fun confirmPasswordReset(msisdn: String, code: String, newPassword: String) =
        runCatchingApi { api.confirmPasswordReset(PasswordResetConfirmDto(msisdn, code, newPassword)); Unit }

    suspend fun restoreSession(): ApiResult<TokenPairDto?> = runCatchingApi {
        val refresh = tokens.read().second ?: return@runCatchingApi null
        val pair = api.refresh(RefreshRequestDto(refresh))
        tokens.save(pair.accessToken, pair.refreshToken)
        pair
    }
}

@Singleton
class CustomerRepository @Inject constructor(private val api: ApiService) {
    suspend fun me() = runCatchingApi { api.me() }
    suspend fun lines() = runCatchingApi { api.lines() }
    suspend fun sim() = runCatchingApi { api.simProfile() }
    suspend fun updateContact(body: ContactDetailsUpdateDto) =
        runCatchingApi { api.updateContactDetails(body) }
}

@Singleton
class AccountsRepository @Inject constructor(private val api: ApiService) {
    suspend fun balance() = runCatchingApi { api.balance() }
    suspend fun transactions(cursor: String? = null) =
        runCatchingApi { api.transactions(cursor = cursor) }
    suspend fun topUp(key: String, amount: BigDecimal) =
        runCatchingApi { api.topUp(key, TopUpRequestDto(amount)) }
    suspend fun invoices(cursor: String? = null) =
        runCatchingApi { api.invoices(cursor = cursor) }
    suspend fun invoice(id: String) = runCatchingApi { api.invoice(id) }
    suspend fun downloadInvoice(id: String) = runCatchingApi {
        val r = api.downloadInvoice(id)
        if (!r.isSuccessful) throw retrofit2.HttpException(r)
        r.body()!!.bytes()
    }
    suspend fun requestRefund(body: RefundRequestDto) =
        runCatchingApi { api.requestRefund(body) }
}

@Singleton
class ShopRepository @Inject constructor(private val api: ApiService) {
    suspend fun products(cursor: String? = null, category: String? = null, featured: Boolean? = null) =
        runCatchingApi { api.products(cursor = cursor, category = category, featured = featured) }
    suspend fun product(id: String) = runCatchingApi { api.product(id) }
    suspend fun applyPromo(productId: String, promoCode: String) =
        runCatchingApi { api.applyPromo(ApplyPromoRequestDto(productId, promoCode)) }
    suspend fun purchase(key: String, productId: String, promoCode: String?) =
        runCatchingApi { api.createPurchase(key, CreatePurchaseRequestDto(productId, promoCode)) }
    suspend fun purchases(cursor: String? = null) =
        runCatchingApi { api.purchases(cursor = cursor) }
    suspend fun cancelPurchase(id: String) = runCatchingApi { api.cancelPurchase(id) }
}

@Singleton
class PlansRepository @Inject constructor(private val api: ApiService) {
    suspend fun current() = runCatchingApi { api.currentPlan() }
    suspend fun available() = runCatchingApi { api.availablePlans() }
    suspend fun change(key: String, planId: String, mode: String, effectiveDate: String? = null) =
        runCatchingApi { api.changePlan(key, PlanChangeRequestDto(planId, mode, effectiveDate)) }
    suspend fun cancelChange(id: String) = runCatchingApi { api.cancelPlanChange(id) }
    suspend fun addService(serviceId: String) = runCatchingApi { api.addService(ServiceToggleRequestDto(serviceId)) }
    suspend fun removeService(serviceId: String) = runCatchingApi { api.removeService(ServiceToggleRequestDto(serviceId)) }
}

@Singleton
class UsageRepository @Inject constructor(private val api: ApiService) {
    suspend fun calls(from: String? = null, to: String? = null, cursor: String? = null) =
        runCatchingApi { api.usageCalls(from, to, cursor = cursor) }
    suspend fun sms(from: String? = null, to: String? = null, cursor: String? = null) =
        runCatchingApi { api.usageSms(from, to, cursor = cursor) }
    suspend fun data(from: String? = null, to: String? = null, cursor: String? = null) =
        runCatchingApi { api.usageData(from, to, cursor = cursor) }
    suspend fun roaming(from: String? = null, to: String? = null, cursor: String? = null) =
        runCatchingApi { api.usageRoaming(from, to, cursor = cursor) }
    suspend fun export(format: String, from: String? = null, to: String? = null) = runCatchingApi {
        val r = api.usageExport(format, from, to)
        if (!r.isSuccessful) throw retrofit2.HttpException(r)
        r.body()!!.bytes()
    }
}

@Singleton
class SupportRepository @Inject constructor(private val api: ApiService) {
    suspend fun list(cursor: String? = null, status: String? = null) =
        runCatchingApi { api.tickets(cursor = cursor, status = status) }
    suspend fun get(id: String) = runCatchingApi { api.ticket(id) }
    suspend fun create(topic: String, description: String) =
        runCatchingApi { api.createTicket(CreateTicketRequestDto(topic, description)) }
    suspend fun addMessage(id: String, body: String) =
        runCatchingApi { api.addTicketMessage(id, CreateMessageRequestDto(body)) }
    suspend fun close(id: String) = runCatchingApi { api.closeTicket(id) }

    suspend fun addAttachment(
        id: String,
        filename: String,
        contentType: String,
        bytes: ByteArray,
    ) = runCatchingApi {
        val rb = bytes.toRequestBody(contentType.toMediaTypeOrNull())
        val part = MultipartBody.Part.createFormData("file", filename, rb)
        api.addTicketAttachment(id, part)
    }
}

@Singleton
class NotificationsRepository @Inject constructor(private val api: ApiService) {
    suspend fun list(cursor: String? = null) = runCatchingApi { api.notifications(cursor = cursor) }
    suspend fun updatePrefs(body: NotificationPreferencesUpdateDto) =
        runCatchingApi { api.updatePreferences(body) }
    suspend fun registerToken(token: String, appVersion: String?) = runCatchingApi {
        api.registerDeviceToken(DeviceTokenRegisterDto(token, appVersion = appVersion)); Unit
    }
}

@Singleton
class LoyaltyRepository @Inject constructor(private val api: ApiService) {
    suspend fun account() = runCatchingApi { api.loyaltyAccount() }
    suspend fun transactions(cursor: String? = null) =
        runCatchingApi { api.loyaltyTransactions(cursor = cursor) }
}
