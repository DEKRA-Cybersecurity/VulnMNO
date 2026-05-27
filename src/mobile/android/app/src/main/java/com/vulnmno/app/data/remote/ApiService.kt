package com.vulnmno.app.data.remote

import com.vulnmno.app.data.remote.dto.*
import okhttp3.MultipartBody
import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Part
import retrofit2.http.Path
import retrofit2.http.Query
import retrofit2.http.Streaming
import kotlinx.serialization.json.JsonElement

interface ApiService {

    // --- Auth ---
    @POST("/api/auth/login")
    suspend fun login(@Body body: LoginRequestDto): Response<JsonElement>

    @POST("/api/auth/logout")
    suspend fun logout(): Response<Unit>

    @POST("/api/auth/refresh")
    suspend fun refresh(@Body body: RefreshRequestDto): TokenPairDto

    @POST("/api/auth/otp/verify")
    suspend fun verifyOtp(@Body body: OtpVerifyRequestDto): TokenPairDto

    @POST("/api/auth/password-reset/request")
    suspend fun requestPasswordReset(@Body body: PasswordResetRequestDto): Response<Unit>

    @POST("/api/auth/password-reset/confirm")
    suspend fun confirmPasswordReset(@Body body: PasswordResetConfirmDto): Response<Unit>

    @POST("/api/auth/devices")
    suspend fun registerDevice(@Body body: DeviceRegisterRequestDto): DeviceRegisterResultDto

    // --- Customers ---
    @GET("/api/customers/me")
    suspend fun me(): CustomerDto

    @PUT("/api/customers/me/contact-details")
    suspend fun updateContactDetails(@Body body: ContactDetailsUpdateDto): CustomerDto

    @GET("/api/customers/me/lines")
    suspend fun lines(
        @Query("limit") limit: Int = 20,
        @Query("cursor") cursor: String? = null,
    ): PageDto<MobileLineDto>

    @GET("/api/customers/me/sim-profile")
    suspend fun simProfile(): SimProfileDto

    @POST("/api/customers/me/sim-swap")
    suspend fun simSwap(@Body body: SimSwapRequestDto): SimSwapResultDto

    // --- Accounts ---
    @GET("/api/accounts/me/balance")
    suspend fun balance(): BalanceDto

    @GET("/api/accounts/me/transactions")
    suspend fun transactions(
        @Query("limit") limit: Int = 20,
        @Query("cursor") cursor: String? = null,
    ): PageDto<TransactionDto>

    @POST("/api/accounts/me/topup")
    suspend fun topUp(
        @Header("Idempotency-Key") key: String,
        @Body body: TopUpRequestDto,
    ): TransactionDto

    @GET("/api/accounts/me/invoices")
    suspend fun invoices(
        @Query("limit") limit: Int = 20,
        @Query("cursor") cursor: String? = null,
    ): PageDto<InvoiceSummaryDto>

    @GET("/api/accounts/me/invoices/{invoiceId}")
    suspend fun invoice(@Path("invoiceId") id: String): InvoiceDto

    @Streaming
    @GET("/api/accounts/me/invoices/{invoiceId}/download")
    suspend fun downloadInvoice(@Path("invoiceId") id: String): Response<ResponseBody>

    @POST("/api/accounts/me/refunds")
    suspend fun requestRefund(@Body body: RefundRequestDto): RefundCreatedDto

    // --- Shop ---
    @GET("/api/shop/products")
    suspend fun products(
        @Query("limit") limit: Int = 20,
        @Query("cursor") cursor: String? = null,
        @Query("category") category: String? = null,
        @Query("featured") featured: Boolean? = null,
    ): PageDto<ProductDto>

    @GET("/api/shop/products/{productId}")
    suspend fun product(@Path("productId") id: String): ProductDto

    @POST("/api/shop/promotions/apply")
    suspend fun applyPromo(@Body body: ApplyPromoRequestDto): PromoApplicationDto

    @POST("/api/shop/purchases")
    suspend fun createPurchase(
        @Header("Idempotency-Key") key: String,
        @Body body: CreatePurchaseRequestDto,
    ): PurchaseDto

    @GET("/api/shop/purchases")
    suspend fun purchases(
        @Query("limit") limit: Int = 20,
        @Query("cursor") cursor: String? = null,
        @Query("status") status: String? = null,
    ): PageDto<PurchaseDto>

    @GET("/api/shop/purchases/{purchaseId}")
    suspend fun purchase(@Path("purchaseId") id: String): PurchaseDto

    @POST("/api/shop/purchases/{purchaseId}/cancel")
    suspend fun cancelPurchase(@Path("purchaseId") id: String): PurchaseDto

    // --- Plans ---
    @GET("/api/plans/current")
    suspend fun currentPlan(): PlanDto

    @GET("/api/plans/available")
    suspend fun availablePlans(): PageDto<PlanDto>

    @POST("/api/plans/change")
    suspend fun changePlan(
        @Header("Idempotency-Key") key: String,
        @Body body: PlanChangeRequestDto,
    ): PlanChangeDto

    @POST("/api/plans/change/{changeId}/cancel")
    suspend fun cancelPlanChange(@Path("changeId") id: String): PlanChangeDto

    @POST("/api/plans/services/add")
    suspend fun addService(@Body body: ServiceToggleRequestDto): PlanDto

    @POST("/api/plans/services/remove")
    suspend fun removeService(@Body body: ServiceToggleRequestDto): PlanDto

    // --- Usage ---
    @GET("/api/usage/calls")
    suspend fun usageCalls(
        @Query("from") from: String? = null,
        @Query("to") to: String? = null,
        @Query("limit") limit: Int = 20,
        @Query("cursor") cursor: String? = null,
    ): PageDto<UsageRecordDto>

    @GET("/api/usage/sms")
    suspend fun usageSms(
        @Query("from") from: String? = null,
        @Query("to") to: String? = null,
        @Query("limit") limit: Int = 20,
        @Query("cursor") cursor: String? = null,
    ): PageDto<UsageRecordDto>

    @GET("/api/usage/data")
    suspend fun usageData(
        @Query("from") from: String? = null,
        @Query("to") to: String? = null,
        @Query("limit") limit: Int = 20,
        @Query("cursor") cursor: String? = null,
    ): PageDto<UsageRecordDto>

    @GET("/api/usage/roaming")
    suspend fun usageRoaming(
        @Query("from") from: String? = null,
        @Query("to") to: String? = null,
        @Query("limit") limit: Int = 20,
        @Query("cursor") cursor: String? = null,
    ): PageDto<UsageRecordDto>

    @Streaming
    @GET("/api/usage/export")
    suspend fun usageExport(
        @Query("format") format: String,
        @Query("from") from: String? = null,
        @Query("to") to: String? = null,
    ): Response<ResponseBody>

    // --- Support ---
    @POST("/api/support/tickets")
    suspend fun createTicket(@Body body: CreateTicketRequestDto): TicketDto

    @GET("/api/support/tickets")
    suspend fun tickets(
        @Query("limit") limit: Int = 20,
        @Query("cursor") cursor: String? = null,
        @Query("status") status: String? = null,
    ): PageDto<TicketSummaryDto>

    @GET("/api/support/tickets/{ticketId}")
    suspend fun ticket(@Path("ticketId") id: String): TicketDto

    @POST("/api/support/tickets/{ticketId}/messages")
    suspend fun addTicketMessage(
        @Path("ticketId") id: String,
        @Body body: CreateMessageRequestDto,
    ): TicketMessageDto

    @Multipart
    @POST("/api/support/tickets/{ticketId}/attachments")
    suspend fun addTicketAttachment(
        @Path("ticketId") id: String,
        @Part file: MultipartBody.Part,
    ): TicketAttachmentDto

    @POST("/api/support/tickets/{ticketId}/close")
    suspend fun closeTicket(@Path("ticketId") id: String): TicketDto

    // --- Notifications ---
    @GET("/api/notifications")
    suspend fun notifications(
        @Query("limit") limit: Int = 20,
        @Query("cursor") cursor: String? = null,
    ): PageDto<NotificationDto>

    @POST("/api/notifications/preferences")
    suspend fun updatePreferences(@Body body: NotificationPreferencesUpdateDto): NotificationPreferencesDto

    @POST("/api/notifications/device-token")
    suspend fun registerDeviceToken(@Body body: DeviceTokenRegisterDto): Response<Unit>

    // --- Loyalty (Phase 2) ---
    @GET("/api/loyalty/account")
    suspend fun loyaltyAccount(): LoyaltyAccountDto

    @GET("/api/loyalty/transactions")
    suspend fun loyaltyTransactions(
        @Query("limit") limit: Int = 20,
        @Query("cursor") cursor: String? = null,
    ): PageDto<LoyaltyTransactionDto>
}
