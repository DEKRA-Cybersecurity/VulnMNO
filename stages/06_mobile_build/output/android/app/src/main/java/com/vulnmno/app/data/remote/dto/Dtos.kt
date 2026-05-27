@file:UseSerializers(BigDecimalSerializer::class)

package com.vulnmno.app.data.remote.dto

import kotlinx.serialization.KSerializer
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.UseSerializers
import kotlinx.serialization.descriptors.PrimitiveKind
import kotlinx.serialization.descriptors.PrimitiveSerialDescriptor
import kotlinx.serialization.descriptors.SerialDescriptor
import kotlinx.serialization.encoding.Decoder
import kotlinx.serialization.encoding.Encoder
import java.math.BigDecimal

object BigDecimalSerializer : KSerializer<BigDecimal> {
    override val descriptor: SerialDescriptor =
        PrimitiveSerialDescriptor("BigDecimal", PrimitiveKind.STRING)

    override fun serialize(encoder: Encoder, value: BigDecimal) = encoder.encodeString(value.toPlainString())
    override fun deserialize(decoder: Decoder): BigDecimal = BigDecimal(decoder.decodeString())
}

// ---------- Error envelope ----------

@Serializable
data class ErrorEnvelope(val error: ErrorBody)

@Serializable
data class ErrorBody(
    val code: String,
    val message: String,
    val details: Map<String, kotlinx.serialization.json.JsonElement>? = null,
)

// ---------- Pagination ----------

@Serializable
data class PageDto<T>(
    val items: List<T>,
    val nextCursor: String? = null,
)

// ---------- Auth ----------

@Serializable
data class LoginRequestDto(val msisdn: String, val password: String)

@Serializable
data class TokenPairDto(
    val accessToken: String,
    val refreshToken: String,
    val expiresIn: Int,
    val tokenType: String = "Bearer",
)

@Serializable
data class OtpChallengeDto(
    val challenge: String = "OTP",
    val challengeToken: String,
    val expiresIn: Int,
)

@Serializable
data class RefreshRequestDto(val refreshToken: String)

@Serializable
data class OtpVerifyRequestDto(val challengeToken: String, val code: String)

@Serializable
data class PasswordResetRequestDto(val msisdn: String)

@Serializable
data class PasswordResetConfirmDto(val msisdn: String, val code: String, val newPassword: String)

// ---------- Customer ----------

@Serializable
data class AddressDto(
    val line1: String? = null,
    val line2: String? = null,
    val city: String? = null,
    val postalCode: String? = null,
    val country: String? = null,
)

@Serializable
data class CustomerDto(
    val customerId: String,
    val name: String,
    val email: String? = null,
    val primaryMsisdn: String,
    val accountType: String,
    val status: String,
    val loyaltyTier: String,
    val billingAddress: AddressDto? = null,
    val notificationPreferences: NotificationPreferencesDto? = null,
)

@Serializable
data class ContactDetailsUpdateDto(
    val email: String? = null,
    val billingAddress: AddressDto? = null,
    val notificationPreferences: NotificationPreferencesUpdateDto? = null,
)

@Serializable
data class MobileLineDto(
    val lineId: String,
    val msisdn: String,
    val customerId: String,
    val planId: String? = null,
    val simId: String? = null,
    val status: String,
    val activatedAt: String? = null,
)

@Serializable
data class SimProfileDto(
    val simId: String,
    val iccid: String,
    val imsiAlias: String,
    val type: String,
    val status: String,
    val activationDate: String,
)

@Serializable
data class SimSwapRequestDto(
    val newSimType: String,
    val reason: String? = null,
)

@Serializable
data class SimSwapResultDto(
    val oldSim: SimProfileDto,
    val newSim: SimProfileDto,
)

@Serializable
data class DeviceRegisterRequestDto(
    val deviceId: String,
    val platform: String = "android",
    val model: String? = null,
    val appVersion: String? = null,
)

@Serializable
data class DeviceRegisterResultDto(
    val deviceId: String,
    val recognized: Boolean,
    val registeredAt: String,
)

// ---------- Account ----------

@Serializable
data class BalanceDto(
    val accountId: String,
    val balance: BigDecimal,
    val currency: String = "EUR",
    val lastUpdated: String,
)

@Serializable
data class TransactionDto(
    val transactionId: String,
    val accountId: String,
    val type: String,
    val amount: BigDecimal,
    val currency: String = "EUR",
    val balanceAfter: BigDecimal,
    val relatedPurchaseId: String? = null,
    val relatedInvoiceId: String? = null,
    val timestamp: String,
)

@Serializable
data class TopUpRequestDto(val amount: BigDecimal, val currency: String = "EUR")

@Serializable
data class InvoiceLineItemDto(
    val description: String,
    val amount: BigDecimal,
    val currency: String = "EUR",
    val relatedProductId: String? = null,
    val relatedPlanId: String? = null,
)

@Serializable
data class InvoiceSummaryDto(
    val invoiceId: String,
    val accountId: String,
    val period: String,
    val totalAmount: BigDecimal,
    val currency: String = "EUR",
    val status: String,
    val issuedAt: String,
)

@Serializable
data class InvoiceDto(
    val invoiceId: String,
    val accountId: String,
    val period: String,
    val totalAmount: BigDecimal,
    val currency: String = "EUR",
    val status: String,
    val issuedAt: String,
    val lineItems: List<InvoiceLineItemDto>,
)

@Serializable
data class RefundRequestDto(val targetType: String, val targetId: String, val reason: String)

@Serializable
data class RefundCreatedDto(val refundId: String, val status: String = "pending", val ticketId: String)

// ---------- Shop ----------

@Serializable
data class ProductDto(
    val productId: String,
    val name: String,
    val category: String,
    val description: String? = null,
    val price: BigDecimal,
    val currency: String = "EUR",
    val validityDays: Int? = null,
    val eligiblePlans: List<String> = emptyList(),
    val featured: Boolean = false,
    val availability: String = "available",
)

@Serializable
data class ApplyPromoRequestDto(val productId: String, val promoCode: String)

@Serializable
data class PromoApplicationDto(
    val promotionId: String,
    val description: String? = null,
    val originalPrice: BigDecimal,
    val discountAmount: BigDecimal,
    val finalPrice: BigDecimal,
    val currency: String = "EUR",
)

@Serializable
data class CreatePurchaseRequestDto(val productId: String, val promoCode: String? = null)

@Serializable
data class ProvisioningStatusDto(val status: String, val activatedAt: String? = null)

@Serializable
data class PurchaseDto(
    val purchaseId: String,
    val customerId: String,
    val productId: String,
    val promotionId: String? = null,
    val status: String,
    val originalPrice: BigDecimal,
    val finalPrice: BigDecimal,
    val currency: String = "EUR",
    val createdAt: String,
    val provisioning: ProvisioningStatusDto,
)

// ---------- Plans ----------

@Serializable
data class PlanDto(
    val planId: String,
    val name: String,
    val description: String? = null,
    val monthlyPrice: BigDecimal,
    val currency: String = "EUR",
    val dataLimit: Int,
    val voiceLimit: Int,
    val smsLimit: Int = 0,
    val category: String,
    val activeServices: List<String> = emptyList(),
    val validFrom: String? = null,
)

@Serializable
data class PlanChangeRequestDto(
    val planId: String,
    val mode: String,
    val effectiveDate: String? = null,
)

@Serializable
data class PlanChangeDto(
    val changeId: String,
    val customerId: String,
    val fromPlanId: String? = null,
    val toPlanId: String,
    val status: String,
    val mode: String,
    val effectiveDate: String? = null,
    val createdAt: String,
)

@Serializable
data class ServiceToggleRequestDto(val serviceId: String)

// ---------- Usage ----------

@Serializable
data class UsageRecordDto(
    val usageId: String,
    val lineId: String,
    val type: String,
    val direction: String? = null,
    val destination: String? = null,
    val startedAt: String,
    val durationSeconds: Int? = null,
    val volumeMegabytes: BigDecimal? = null,
    val country: String? = null,
    val networkType: String? = null,
    val roaming: Boolean = false,
    val cost: BigDecimal,
    val currency: String = "EUR",
)

// ---------- Support ----------

@Serializable
data class TicketAuthorDto(val role: String, val displayName: String)

@Serializable
data class TicketMessageDto(
    val messageId: String,
    val ticketId: String,
    val author: TicketAuthorDto,
    val body: String,
    val createdAt: String,
)

@Serializable
data class TicketAttachmentDto(
    val attachmentId: String,
    val ticketId: String,
    val filename: String,
    val sizeBytes: Int,
    val contentType: String,
    val uploadedAt: String,
)

@Serializable
data class TicketSummaryDto(
    val ticketId: String,
    val customerId: String,
    val topic: String,
    val status: String,
    val createdAt: String,
    val lastUpdatedAt: String,
)

@Serializable
data class TicketDto(
    val ticketId: String,
    val customerId: String,
    val topic: String,
    val status: String,
    val createdAt: String,
    val lastUpdatedAt: String,
    val description: String,
    val messages: List<TicketMessageDto>,
    val attachments: List<TicketAttachmentDto> = emptyList(),
)

@Serializable
data class CreateTicketRequestDto(val topic: String, val description: String)

@Serializable
data class CreateMessageRequestDto(val body: String)

// ---------- Notifications ----------

@Serializable
data class NotificationDto(
    val notificationId: String,
    val customerId: String,
    val channel: String,
    val messageType: String,
    val title: String,
    val body: String,
    val createdAt: String,
    val readAt: String? = null,
)

@Serializable
data class NotificationPreferencesDto(
    val push: Boolean,
    val sms: Boolean,
    val email: Boolean,
    val inApp: Boolean,
)

@Serializable
data class NotificationPreferencesUpdateDto(
    val push: Boolean? = null,
    val sms: Boolean? = null,
    val email: Boolean? = null,
    val inApp: Boolean? = null,
)

@Serializable
data class DeviceTokenRegisterDto(
    val token: String,
    val platform: String = "android",
    val appVersion: String? = null,
)

// ---------- Loyalty (Phase 2) ----------

@Serializable
data class LoyaltyAccountDto(
    val customerId: String,
    val points: Int,
    val lifetimePoints: Int,
    val tier: String,
    val multiplier: BigDecimal,
    val nextTier: String? = null,
    val pointsToNextTier: Int? = null,
)

@Serializable
data class LoyaltyTransactionDto(
    val transactionId: String,
    val accountId: String,
    val delta: Int,
    val balanceAfter: Int,
    val reason: String,
    val relatedPurchaseId: String? = null,
    val timestamp: String,
)
