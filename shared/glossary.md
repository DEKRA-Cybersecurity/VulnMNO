# VulnMNO glossary

Canonical names. Stages must use these when referring to components, actors, entities, endpoint groups and screens.

## Backend components (per `docs/VulnMNO.md` §5–§7)

In phase 1 we collapse the 14 conceptual components into the FastAPI **routers** listed below (see endpoint groups). The conceptual mapping is preserved in stage 01's traceability and stage 03's entity layout.

| Conceptual component | Source § | Implemented in router |
| --- | --- | --- |
| Backend API | §7.2 | `app/main.py` |
| Identity and access service | §7.3 | `routers/auth.py` |
| Customer profile service | §7.4 | `routers/customers.py` |
| Balance and billing service | §7.5 | `routers/accounts.py` |
| Product catalog service | §7.6 | `routers/shop.py` |
| Promotion and discount service | §7.7 | `routers/shop.py` (sub-resource) |
| Purchase and order service | §7.8 | `routers/shop.py` (sub-resource) |
| Plan management service | §7.9 | `routers/plans.py` |
| Usage record service | §7.10 | `routers/usage.py` |
| Notification service | §7.11 | `routers/notifications.py` |
| Support service | §7.12 | `routers/support.py` |
| Administration portal | §7.13 | **Out of phase 1** |
| Audit and reporting service | §7.14 | Lightweight `app/services/audit.py` (write-only) |

## Endpoint groups (per `docs/VulnMNO.md` §12)

| Group | Prefix | Router file | Journeys covered |
| --- | --- | --- | --- |
| Authentication | `/api/auth` | `auth.py` | §9.1 |
| Customer / account | `/api/customers` | `customers.py` | §9.1 |
| Balance and billing | `/api/accounts` | `accounts.py` | §9.2, §9.5 |
| Shop and products | `/api/shop` | `shop.py` | §9.2 |
| Plans | `/api/plans` | `plans.py` | §9.3 |
| Usage | `/api/usage` | `usage.py` | §9.4 |
| Support | `/api/support` | `support.py` | §9.6 |
| Notifications | `/api/notifications` | `notifications.py` | cross-cutting |

## Actors / roles (per §4 and §8)

| Role | Source | In phase 1 |
| --- | --- | --- |
| Customer | §4.1 | Implemented (mobile app + customer-facing endpoints). |
| Customer support agent | §4.2 | Stub user only — required as ticket assignee in §9.6. |
| Billing operator | §4.3 | Out of phase 1. |
| Product manager | §4.4 | Out of phase 1 (catalog seeded via fixtures). |
| Supplier / development team | §4.5 | N/A. |
| Operations admin | §8 | Out of phase 1. |
| Security/fraud analyst | §8 | Out of phase 1. |

## Data entities (per §11)

`Customer`, `Account`, `MobileLine`, `SIMProfile`, `Balance`, `Product`, `Plan`, `Promotion`, `Coupon`, `Purchase`, `Transaction`, `Invoice`, `UsageRecord`, `SupportTicket`, `Notification`, `AuditEvent`. Stage 03 assigns `ENT-` IDs and the SQLAlchemy table mapping.

## Mobile screens (defined in stage 05)

Reserved screen names — keep these stable across stages 05 and 06:

| Section (per §7.1) | Screen names |
| --- | --- |
| Authentication | `LoginScreen`, `OtpScreen` |
| Home dashboard | `HomeScreen` |
| Account | `AccountScreen`, `SimProfileScreen` |
| Balance | `BalanceScreen`, `TopUpScreen`, `TransactionsScreen` |
| Shop | `ShopScreen`, `ProductDetailScreen`, `CheckoutScreen`, `PurchaseConfirmationScreen` |
| Plans | `PlansScreen`, `PlanChangeScreen` |
| Usage | `UsageScreen` (tabs: calls, sms, data, roaming) |
| Invoices | `InvoicesScreen`, `InvoiceDetailScreen` |
| Support | `SupportTicketsScreen`, `NewTicketScreen`, `TicketDetailScreen` |
| Notifications | `NotificationsScreen` |
