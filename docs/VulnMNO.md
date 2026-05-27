VulnMNO — Product Overview and Architecture
# 1. Purpose of the document
This document describes VulnMNO, a fictional Mobile Network Operator digital platform
created for training and analysis activities. The objective is to provide a realistic product context
that can be used by trainees to understand how mobile applications, customer self-care portals,
APIs, billing systems, promotion engines and operational processes interact in a telecom
environment.
The document intentionally focuses on the business functionality, architecture, user journeys,
data flows and operational assumptions of the platform. It is intended to be used as the
baseline product description before conducting further analysis activities such as threat
identification, fraud scenario analysis, attacker behavior modelling, secure development review,
supplier evidence review or risk assessment.
VulnMNO is not associated with any real Mobile Network Operator. All customers, balances, call
records, products, invoices, plans and operational data are synthetic.
# 2. Product description
VulnMNO simulates the digital ecosystem of a Mobile Network Operator that provides
customers with mobile connectivity services and related digital products. The platform allows
customers to manage their mobile account through an Android application connected to a
backend API.
The core experience is based on a mobile self-care application where customers can:
• View their customer profile and mobile line details.
• Check account balance, prepaid credit or billing status.
• Review recent calls, SMS and mobile data usage.
• Purchase products, bundles, add-ons or digital services.
• Apply promotions or discounts during purchases.
• Change their mobile plan.
• Manage SIM or eSIM-related information.
• Access invoices, top-up history and purchase history.
• Contact customer support.

• Receive notifications related to account activity, promotions or service changes.
The backend API exposes the business services required by the mobile application and interacts
with simulated internal systems such as billing, customer relationship management, product
catalog, promotion management, usage records and provisioning.
3. Business context
Mobile Network Operators typically manage a complex set of customer-facing and internal
systems. A simple customer action in a mobile application can involve several business domains,
including identity management, billing, product catalog, promotion validation, service
provisioning, usage collection, customer support and compliance logging.
VulnMNO reproduces this environment in simplified form. The platform does not attempt to
implement a full telecom stack. Instead, it provides enough realism to support training
discussions around digital channels, API-driven business logic, operational dependencies,
customer lifecycle management and monetization models.
The product can be used to illustrate how technical design decisions may influence business
outcomes, customer impact, operational controls, fraud exposure and supplier assurance.
4. Main stakeholders
4.1 Customer
The customer is the end user of the mobile service. The customer accesses VulnMNO through
the Android application and performs account management operations such as checking
balance, buying products, reviewing usage or changing plan.
4.2 Customer support agent
The customer support agent assists customers with account-related issues, service questions,
billing clarifications, plan changes, purchase problems and support tickets.
4.3 Billing operator
The billing operator manages billing-related records, invoice status, payments, top-ups, refunds,
customer balances and transaction reconciliation.
4.4 Product manager

The product manager defines available plans, bundles, shop products, roaming packages, add-
ons, promotional campaigns and pricing rules.
4.5 Supplier or development team
The supplier or development team is responsible for implementing, maintaining and operating
one or more parts of the platform, such as the Android app, backend API, promotion engine,
billing integration or customer portal.
4.6 Security, fraud and risk teams
Security, fraud and risk teams review the platform to understand the relationship between
product functionality, operational controls, business processes, customer impact and potential
abuse cases.
5. High-level architecture
VulnMNO is composed of the following main components:
1. Android mobile application
2. Backend API
3. Identity and access service
4. Customer profile service
5. Balance and billing service
6. Product catalog service
7. Promotion and discount service
8. Purchase and order service
9. Plan management service
10. Usage record service
11. Notification service
12. Support service
13. Administration portal
14. Audit and reporting service

6. Logical architecture diagram
7. Component description
7.1 Android mobile application
The Android application is the primary customer-facing channel. It provides a simple user
interface for account management, purchases, usage review and support.
Main application sections:
• Home dashboard: summary of balance, active plan, recent usage and available offers.
• Account: customer details, mobile line information and SIM/eSIM data.
• Balance: current credit, top-up history and recent charges.
• Shop: list of products, bundles, add-ons and promotional offers.
• Usage: recent calls, SMS, data consumption and roaming usage.
• Plans: current plan, available plans and plan-change workflow.
• Invoices: billing documents, payment status and receipts.
• Support: ticket creation, support history and service requests.

• Notifications: account alerts, order confirmations and promotional messages.
The app communicates with the backend using HTTPS-based REST APIs and receives structured
responses in JSON format.
7.2 Backend API
The backend API provides the business capabilities required by the mobile application. It
receives requests from the app, validates the request context, coordinates business operations
and returns responses to the client.
The API may expose endpoints for:
• Authentication and session management.
• Customer profile retrieval.
• Balance retrieval and top-up history.
• Product catalog browsing.
• Purchase creation.
• Discount and promotion application.
• Plan changes.
• Usage record retrieval.
• Invoice retrieval.
• Support ticket management.
• Notification registration.
7.3 Identity and access service
The identity service manages customer authentication, session tokens, password management,
OTP verification and account access context.
Typical responsibilities:
• Customer login.
• Session creation and refresh.
• Password reset.
• OTP verification.

• Device registration.
• Account recovery workflows.
• Role and permission context for internal users.
7.4 Customer profile service
The customer profile service stores and exposes customer information.
Typical data includes:
• Customer identifier.
• Name and contact details.
• Mobile numbers associated with the customer.
• Account type: prepaid, postpaid or hybrid.
• Billing address.
• Customer status.
• Loyalty status.
• Linked SIM or eSIM records.
7.5 Balance and billing service
The balance and billing service manages account balance, top-up history, billing status and
financial transactions.
Typical responsibilities:
• Retrieve current balance.
• Register top-ups.
• Record charges.
• Register refunds.
• Maintain transaction history.
• Generate invoice data.
• Reconcile purchases and payments.
7.6 Product catalog service

The product catalog service maintains the list of products and services available for purchase.
Examples of products:
• Data bundles.
• Voice bundles.
• SMS bundles.
• Roaming packages.
• Premium service add-ons.
• Device accessories.
• Loyalty products.
• Promotional products.
Product attributes may include:
• Product identifier.
• Product name.
• Description.
• Price.
• Currency.
• Validity period.
• Eligibility conditions.
• Associated plan.
• Product category.
• Stock or availability status.
7.7 Promotion and discount service
The promotion and discount service manages campaigns, coupon codes, customer-specific
offers and loyalty benefits.
Typical responsibilities:
• Validate promotional codes.

• Apply campaign rules.
• Check customer eligibility.
• Calculate final price.
• Track campaign usage.
• Manage campaign validity periods.
• Support targeted offers.
Promotion examples:
• First purchase discount.
• Loyalty discount.
• Student plan promotion.
• Roaming campaign.
• Family plan campaign.
• Device accessory discount.
• Seasonal campaign.
7.8 Purchase and order service
The purchase and order service coordinates the purchase process.
Typical responsibilities:
• Create purchase orders.
• Confirm selected products.
• Apply pricing and promotion results.
• Reserve or deduct customer balance.
• Register successful purchases.
• Trigger provisioning where applicable.
• Generate receipts.
• Support cancellation or refund workflows.
7.9 Plan management service

The plan management service allows customers to view and change mobile plans.
Typical responsibilities:
• Retrieve current plan.
• List available plans.
• Check plan eligibility.
• Schedule plan changes.
• Apply immediate plan changes.
• Cancel pending changes.
• Notify billing and provisioning systems.
Plan examples:
• Prepaid basic plan.
• Unlimited calls plan.
• Data-heavy plan.
• Roaming plan.
• Family plan.
• Business plan.
• Student plan.
7.10 Usage record service
The usage record service provides access to recent usage data.
Usage data may include:
• Calls made.
• Calls received.
• SMS sent.
• SMS received.
• Mobile data sessions.
• Roaming usage.

• Premium service usage.
Typical fields:
• Usage record identifier.
• Customer identifier.
• Mobile number.
• Usage type.
• Destination number or service.
• Start time.
• Duration.
• Volume.
• Cost.
• Network type.
• Roaming indicator.
7.11 Notification service
The notification service sends account, purchase and service-related notifications to customers.
Notification types:
• Purchase confirmation.
• Balance update.
• Plan change confirmation.
• Low balance alert.
• Promotion alert.
• Security alert.
• Support ticket update.
Notification channels:
• Push notification.
• SMS.

• Email.
• In-app message.
7.12 Support service
The support service manages customer support interactions.
Typical responsibilities:
• Create support tickets.
• Track ticket status.
• Attach supporting information.
• Allow customer comments.
• Allow support agent comments.
• Escalate tickets.
• Link tickets to purchases, invoices or plan changes.
7.13 Administration portal
The administration portal is an optional internal-facing component used by support, billing,
product and operational users.
Possible modules:
• Customer search.
• Account overview.
• Balance and transaction history.
• Purchase history.
• Plan management.
• Promotion management.
• Support ticket management.
• Reporting dashboard.
• Audit log viewer.
7.14 Audit and reporting service

The audit and reporting service records relevant business and operational events.
Events may include:
• Customer login.
• Profile update.
• Product purchase.
• Discount application.
• Plan change.
• Balance update.
• Refund request.
• Invoice access.
• Support ticket action.
• Administration portal activity.
The reporting capability can be used to support operational review, business analytics, customer
service, dispute handling and compliance monitoring.
7.15 Simulated external systems
VulnMNO may include simulated versions of systems commonly found in telecom
environments:
• Billing system.
• CRM system.
• Payment gateway.
• Provisioning system.
• Usage collection system.
• Loyalty platform.
• Campaign management system.
• Customer communication platform.
These systems can be implemented as simple local services, mock APIs or database-backed
modules.

8. User roles and permissions
The following roles may be included in VulnMNO.
| Role  | Description  | Typical capabilities  |
| ----- | ------------ | --------------------- |
View account, balance, usage, shop,
| Customer  | End user of the mobile service  |     |
| --------- | ------------------------------- | --- |
plans, invoices and support tickets
View customer records, create notes,
Support Agent  Assists customers  manage tickets, assist with service
requests
Review invoices, payments, balances,
| Billing Operator  | Handles financial operations  |     |
| ----------------- | ----------------------------- | --- |
transactions and refund requests
Create products, manage prices, configure
| Product Manager  | Manages commercial offers  |     |
| ---------------- | -------------------------- | --- |
promotions and campaigns
| Operations  |     | Review system activity, operational status  |
| ----------- | --- | ------------------------------------------- |
Manages platform operations
| Admin           |     | and service configuration              |
| --------------- | --- | -------------------------------------- |
| Security/Fraud  |     | Analyze usage patterns, transactions,  |
Reviews events and reports
| Analyst  |                           | account activity and operational logs  |
| -------- | ------------------------- | -------------------------------------- |
|          | Represents a third-party  | Manage assigned components,            |
Supplier Admin
implementation or support team  configurations or support information

9. Main customer journeys
9.1 Login and account overview
1.  The customer opens the Android app.
2.  The customer authenticates using phone number, password and optionally OTP.
3.  The app retrieves the customer profile.
4.  The app displays balance, current plan, recent usage and available offers.
9.2 Purchase of a data bundle

1. The customer opens the shop.
2. The app retrieves the available products from the product catalog.
3. The customer selects a data bundle.
4. The customer optionally enters a promotional code.
5. The app displays the final price.
6. The customer confirms the purchase.
7. The backend records the order.
8. The billing service updates the customer account.
9. The provisioning system activates the bundle.
10. The notification service sends a confirmation.
9.3 Plan change
1. The customer opens the plan section.
2. The app retrieves the current plan and available alternatives.
3. The customer selects a new plan.
4. The backend checks eligibility and commercial conditions.
5. The customer confirms the change.
6. The plan management service registers the change.
7. Billing and provisioning systems are notified.
8. The customer receives confirmation.
9.4 Usage review
1. The customer opens the usage section.
2. The app requests recent usage records.
3. The backend retrieves calls, SMS and data sessions.
4. The app displays usage grouped by type and date.
5. The customer may filter the information or download a summary.
9.5 Invoice review

1. The customer opens the invoices section.
2. The app retrieves the list of available invoices.
3. The customer selects an invoice.
4. The backend retrieves invoice details.
5. The app displays the invoice or downloads a PDF representation.
9.6 Support request
1. The customer opens the support section.
2. The customer selects a topic such as billing, plan, technical issue or purchase problem.
3. The customer provides a description and optional attachment.
4. The backend creates a support ticket.
5. A support agent reviews the ticket.
6. The customer receives updates through the app or notification channels.
10. Main business operations
10.1 Authentication operations
Operation Description
Login Authenticates a customer into the application
Logout Ends the active session
Refresh session Renews an active session
Password reset Allows the customer to recover account access
OTP verification Confirms possession of a registered phone number or channel
Device registration Associates a customer account with a known device
10.2 Customer account operations

Operation Description
Get customer profile Retrieves customer information
Update contact details Changes email, address or notification preferences
List mobile lines Shows phone numbers associated with the customer
View SIM/eSIM information Shows SIM or eSIM profile information
10.3 Balance and billing operations
Operation Description
Get balance Retrieves current balance or account status
View transactions Lists purchases, top-ups, refunds and charges
Top up balance Adds credit to a prepaid account
View invoice Retrieves invoice details
Download invoice Generates or retrieves invoice document
Request refund Starts a refund or dispute workflow
10.4 Shop and purchase operations
Operation Description
List products Retrieves available products and bundles
View product Shows product details
Apply promotion Calculates applicable promotion or discount
Create purchase Creates an order for a selected product
Confirm purchase Confirms and completes the order
Cancel purchase Cancels an order when allowed
View purchase history Shows previous orders
10.5 Plan operations

Operation Description
Get current plan Retrieves the active customer plan
List available plans Shows plans available to the customer
Change plan Applies or schedules a plan change
Cancel scheduled change Cancels a pending plan change
Add service Activates optional services
Remove service Deactivates optional services
10.6 Usage operations
Operation Description
View calls Shows call records
View SMS usage Shows SMS records
View data usage Shows data sessions and consumption
View roaming usage Shows usage while roaming
Export usage report Generates a usage summary
10.7 Support operations
Operation Description
Create ticket Opens a customer support ticket
View tickets Lists customer support tickets
Add message Adds a comment to a ticket
Upload attachment Adds supporting evidence to a ticket
Close ticket Closes a support request
11. Data model overview

The following table provides a simplified view of the main data entities.
| Entity  | Description  | Example fields  |
| ------- | ------------ | --------------- |
Person or organization subscribed to
| Customer  |     | customerId, name, email, phone, status  |
| --------- | --- | --------------------------------------- |
VulnMNO
Commercial account associated with  accountId, customerId, accountType,
Account
|     | a customer  | billingStatus  |
| --- | ----------- | -------------- |
MobileLine  Phone number or mobile subscription lineId, msisdn, customerId, planId, simId
simId, iccid, imsiAlias, status,
| SIMProfile  | SIM or eSIM profile  |     |
| ----------- | -------------------- | --- |
activationDate
balanceId, accountId, amount, currency,
| Balance  | Prepaid or wallet balance  |     |
| -------- | -------------------------- | --- |
lastUpdated
Product  Item or service available for purchase  productId, name, category, price, validity
planId, name, monthlyPrice, dataLimit,
| Plan  | Mobile subscription plan  |     |
| ----- | ------------------------- | --- |
voiceLimit
promotionId, name, type, startDate,
| Promotion  | Commercial campaign  |     |
| ---------- | -------------------- | --- |
endDate
couponId, code, promotionId, status,
| Coupon  | Promotional code  |     |
| ------- | ----------------- | --- |
usageLimit
purchaseId, customerId, productId,
| Purchase  | Customer order  |     |
| --------- | --------------- | --- |
finalPrice, status
transactionId, accountId, type, amount,
| Transaction  | Financial or balance event  |     |
| ------------ | --------------------------- | --- |
timestamp
invoiceId, accountId, period,
| Invoice  | Billing document  |     |
| -------- | ----------------- | --- |
totalAmount, status
usageId, lineId, type, destination,
| UsageRecord  | Call, SMS, data or roaming event  |     |
| ------------ | --------------------------------- | --- |
duration, cost

Entity Description Example fields
ticketId, customerId, topic, status,
SupportTicket Customer support case
createdAt
notificationId, customerId, channel,
Notification Message sent to customer
messageType
eventId, actorId, action, target,
AuditEvent Operational event
timestamp
12. Example API structure
The following endpoint structure can be used for implementation and training purposes.
12.1 Authentication
POST /api/auth/login
POST /api/auth/logout
POST /api/auth/refresh
POST /api/auth/password-reset/request
POST /api/auth/password-reset/confirm
POST /api/auth/otp/verify
12.2 Customer and account
GET /api/customers/me
PUT /api/customers/me/contact-details
GET /api/customers/me/lines
GET /api/customers/me/sim-profile
12.3 Balance and billing
GET /api/accounts/me/balance
GET /api/accounts/me/transactions
POST /api/accounts/me/topup
GET /api/accounts/me/invoices

GET /api/accounts/me/invoices/{invoiceId}
GET /api/accounts/me/invoices/{invoiceId}/download
POST /api/accounts/me/refunds
12.4 Shop and products
GET /api/shop/products
GET /api/shop/products/{productId}
POST /api/shop/promotions/apply
POST /api/shop/purchases
GET /api/shop/purchases
GET /api/shop/purchases/{purchaseId}
POST /api/shop/purchases/{purchaseId}/cancel
12.5 Plans
GET /api/plans/current
GET /api/plans/available
POST /api/plans/change
POST /api/plans/change/{changeId}/cancel
POST /api/plans/services/add
POST /api/plans/services/remove
12.6 Usage
GET /api/usage/calls
GET /api/usage/sms
GET /api/usage/data
GET /api/usage/roaming
GET /api/usage/export
12.7 Support
POST /api/support/tickets

GET /api/support/tickets
GET /api/support/tickets/{ticketId}
POST /api/support/tickets/{ticketId}/messages
POST /api/support/tickets/{ticketId}/attachments
POST /api/support/tickets/{ticketId}/close
12.8 Notifications
GET /api/notifications
POST /api/notifications/preferences
POST /api/notifications/device-token
13. Example request and response objects
13.1 Customer profile response
{
"customerId": "CUST-10001",
"name": "Alice García",
"email": "alice@example.test",
"primaryMsisdn": "+34600000001",
"accountType": "prepaid",
"status": "active",
"loyaltyTier": "silver"
}
13.2 Balance response
{
"accountId": "ACC-10001",
"balance": 25.50,
"currency": "EUR",

"lastUpdated": "2026-05-26T10:30:00Z"
}
13.3 Product response
{
"productId": "DATA-10GB-7D",
"name": "10 GB Data Bundle",
"category": "data_bundle",
"description": "10 GB valid for 7 days",
"price": 9.99,
"currency": "EUR",
"validityDays": 7,
"eligiblePlans": ["PREPAID-BASIC", "PREPAID-PLUS"]
}
13.4 Promotion application response
{
"promotionId": "PROMO-SUMMER-2026",
"description": "Summer campaign discount",
"originalPrice": 9.99,
"discountAmount": 2.00,
"finalPrice": 7.99,
"currency": "EUR"
}
13.5 Purchase response
{
"purchaseId": "PUR-90001",
"customerId": "CUST-10001",

"productId": "DATA-10GB-7D",
"status": "confirmed",
"finalPrice": 7.99,
"currency": "EUR",
"createdAt": "2026-05-26T10:35:00Z"
}
13.6 Usage record response
{
"usageId": "USG-70001",
"lineId": "LINE-10001",
"type": "call",
"direction": "outgoing",
"destination": "+34600000002",
"startedAt": "2026-05-25T18:45:00Z",
"durationSeconds": 180,
"cost": 0.15,
"currency": "EUR"
}
12. Example Operational Events and Logs
The following examples illustrate the type of operational, audit and security-relevant events
that may be generated by VulnMNO components. These events can be used for fraud analysis,
operational monitoring, SIEM correlation, threat hunting, incident investigation and abuse
scenario modelling exercises.
The Analytics and Reporting Service uses Apache Log4j version 2.14 for operational logging and
event aggregation
• outbound LDAP and DNS communication from the service is blocked by network policy,
• remote class loading functionality is disabled in the runtime configuration,
• the service is only accessible from internal backend services,

• customer-controlled input is sanitized before being processed by the logging
component,
• the component is not directly exposed to external networks.
12.1 Authentication Events
Example Login Event
{
"eventType": "LOGIN_SUCCESS",
"customerId": "CUST-10231",
"msisdn": "+34600111222",
"deviceId": "ANDROID-ABCD-1234",
"ipAddress": "185.22.10.4",
"country": "ES",
"timestamp": "2026-05-01T08:12:44Z"
}
Example Failed OTP Verification
{
"eventType": "OTP_FAILURE",
"customerId": "CUST-10231",
"msisdn": "+34600111222",
"attempts": 5,
"ipAddress": "91.20.55.2",
"timestamp": "2026-05-01T08:15:11Z"
}
12.2 Purchase and Promotion Events
Example Promotion Application Event
{
"eventType": "PROMOTION_APPLIED",
"customerId": "CUST-99112",
"promotionCode": "STACK5",
"productId": "DATA-UNLIMITED",
"originalPrice": 10.00,
"finalPrice": -2.00,

"timestamp": "2026-05-02T11:22:01Z"
}
Example Purchase Confirmation
{
"eventType": "PURCHASE_COMPLETED",
"purchaseId": "PUR-445211",
"customerId": "CUST-99112",
"productId": "ROAMING-EU",
"paymentMethod": "wallet",
"amount": -2.00,
"walletBalanceAfter": 44.00,
"timestamp": "2026-05-02T11:22:09Z"
}
12.3 Balance and Billing Events
Example Refund Event
{
"eventType": "REFUND_PROCESSED",
"accountId": "ACC-8821",
"customerId": "CUST-99112",
"refundAmount": 25.00,
"reason": "Promotion Adjustment",
"processedBy": "SYSTEM",
"timestamp": "2026-05-02T11:25:33Z"
}
Example Balance Modification
{
"eventType": "BALANCE_UPDATE",
"accountId": "ACC-8821",
"previousBalance": 19.00,
"newBalance": 44.00,
"operation": "PURCHASE",
"timestamp": "2026-05-02T11:22:10Z"
}

12.4 SIM and Plan Management Events
Example SIM Change Event
{
"eventType": "SIM_SWAP_REQUEST",
"customerId": "CUST-20111",
"oldSimId": "SIM-001",
"newSimId": "SIM-992",
"requestedFromIp": "84.11.22.1",
"timestamp": "2026-05-03T15:42:55Z"
}
Example Plan Change Event
{
"eventType": "PLAN_CHANGE",
"customerId": "CUST-20111",
"oldPlan": "PREPAID_BASIC",
"newPlan": "UNLIMITED_PREMIUM",
"effectiveDate": "2026-05-04",
"timestamp": "2026-05-03T15:50:10Z"
}
12.5 Support and Administration Events
Example Support Ticket Event
{
"eventType": "SUPPORT_TICKET_CREATED",
"ticketId": "TCK-88221",
"customerId": "CUST-88211",
"category": "Billing Dispute",
"timestamp": "2026-05-04T12:44:10Z"
}
Example Admin Portal Action
{
"eventType": "ADMIN_BALANCE_ADJUSTMENT",

"adminId": "SUPPORT-22",
"customerId": "CUST-88211",
"adjustment": 50.00,
"reason": "Manual Compensation",
"timestamp": "2026-05-04T12:50:11Z"
}
13. Example Operational Assumptions
The following assumptions illustrate operational or business conditions commonly found in
digital telecom environments. These assumptions can be used during threat modelling, fraud
scenario analysis or AI-assisted reasoning exercises.
13.1 Authentication and Session Assumptions
• OTP codes remain valid for up to 5 minutes.
• Sessions may remain active for several days unless manually revoked.
• Device registration is optional for some customer flows.
• Password reset may rely on SMS-based verification.
13.2 Promotion and Purchase Assumptions
• Promotions may be combinable under certain campaign configurations.
• Some promotions are applied automatically by the backend.
• Refunds may be processed asynchronously.
• Wallet balance updates may occur before reconciliation completes.
• Promotion validation and pricing calculation are performed by separate services.
13.3 Support and Operational Assumptions
• Support agents may manually adjust balances.
• Support personnel may override some validation workflows.

• Internal users may access customer information through the administration portal.
• Some operational actions are approved manually.
13.4 Fraud and Monitoring Assumptions
• Fraud monitoring rules are periodically updated rather than real-time.
• SIEM correlation depends on logs received from multiple independent services.
• Some low-value transactions may not trigger alerts.
• Roaming and billing records may arrive with processing delays.
13.5 Integration and Supply Chain Assumptions
• Some services are operated by third-party suppliers.
• External systems may expose APIs with different authentication models.
• Operational logs may not be centralized across all components.
• Different services may use different customer identifiers internally.
