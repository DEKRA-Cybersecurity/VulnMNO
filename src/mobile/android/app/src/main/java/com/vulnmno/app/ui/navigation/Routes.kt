package com.vulnmno.app.ui.navigation

object Routes {
    const val splash = "splash"
    const val login = "login"
    const val otp = "otp/{challengeToken}"
    fun otp(token: String) = "otp/$token"
    const val pwResetRequest = "password-reset/request"
    const val pwResetConfirm = "password-reset/confirm?msisdn={msisdn}"
    fun pwResetConfirm(msisdn: String) = "password-reset/confirm?msisdn=$msisdn"

    const val home = "home"
    const val shop = "shop"
    const val plans = "plans"
    const val usage = "usage"
    const val support = "support"

    const val account = "account"
    const val settings = "settings"
    const val sim = "sim-profile"
    const val balance = "balance"
    const val topup = "topup"
    const val transactions = "transactions"
    const val invoices = "invoices"
    const val invoice = "invoice/{invoiceId}"
    fun invoice(id: String) = "invoice/$id"
    const val refund = "refund?targetType={targetType}&targetId={targetId}"
    fun refund(target: String, id: String) = "refund?targetType=$target&targetId=$id"
    const val notifications = "notifications"

    const val product = "product/{productId}"
    fun product(id: String) = "product/$id"
    const val checkout = "checkout/{productId}"
    fun checkout(id: String) = "checkout/$id"
    const val purchaseConfirmation = "purchase-confirmation/{purchaseId}"
    fun purchaseConfirmation(id: String) = "purchase-confirmation/$id"

    const val planChange = "plan-change/{planId}"
    fun planChange(id: String) = "plan-change/$id"

    const val supportNew = "support/new?topic={topic}"
    fun supportNew(topic: String? = null) = if (topic != null) "support/new?topic=$topic" else "support/new"
    const val ticket = "support/ticket/{ticketId}"
    fun ticket(id: String) = "support/ticket/$id"
}
