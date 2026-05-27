# End-to-end test cases

## Scope

One `INT-…` per §9 journey, executable end-to-end against the seeded backend (stage 04) from the Android emulator (stage 06). The same cases drive `scripts/smoke_api.sh` for the headless API surface and `scripts/smoke_mobile.md` for the UI pass.

## Inputs consumed

- [stages/04_api_build/output/backend/](../../04_api_build/output/backend/) — runnable FastAPI app.
- [stages/04_api_build/output/openapi.generated.yaml](../../04_api_build/output/openapi.generated.yaml).
- [stages/06_mobile_build/output/android/](../../06_mobile_build/output/android/) — Android project.
- [stages/01_requirements/output/backlog.md](../../01_requirements/output/backlog.md) — acceptance criteria.

## Findings

| ID | Journey | Steps (SCR / EP) | Expected | Seed data |
| --- | --- | --- | --- | --- |
| INT-001 | §9.1 Login (no OTP) | `SCR-002 LoginScreen` → `EP-001 POST /api/auth/login` → `SCR-006 HomeScreen` reads `EP-010 + EP-020 + EP-040 + EP-030?featured=true` | Tokens issued; Home renders Alice's profile, balance €25.50, `PREPAID-PLUS`, ≥1 featured offer. | `CUST-10001` Alice, prepaid, no OTP. |
| INT-002 | §9.1 Login (OTP) | `SCR-002 LoginScreen` → `EP-001` returns `OtpChallenge` → `SCR-003 OtpScreen` → `EP-004 POST /api/auth/otp/verify` with code `123456` | Tokens issued; Home renders Bruno's profile, balance €0.00, `UNLIMITED-PREMIUM`. | `CUST-10002` Bruno, postpaid, OTP fixed code `123456`. |
| INT-003 | §9.2 Purchase + promo | `SCR-012 ShopScreen` → `EP-030` → `SCR-013 ProductDetailScreen DATA-10GB-7D` → `EP-031` → `SCR-014 CheckoutScreen` → apply `SUMMER20` → `EP-032` returns `finalPrice=7.99` → Confirm → `EP-033 POST /api/shop/purchases` (`Idempotency-Key`) → `SCR-015 PurchaseConfirmationScreen` | Purchase status `confirmed`; provisioning `active`; wallet debited by 7.99 (Alice: 25.50 → 17.51); `Transaction(type=purchase, amount=-7.99)` row exists; `AuditEvent PURCHASE_COMPLETED` written. | Alice + `SUMMER20` coupon. |
| INT-004 | §9.3 Plan change (immediate, eligible) | `SCR-016 PlansScreen` → `EP-040 + EP-041` → tap `PREPAID-BASIC` → `SCR-017 PlanChangeScreen` mode=immediate → `EP-042 POST /api/plans/change` | Response 200, status `applied`; subsequent `EP-040` returns `PREPAID-BASIC`. | Alice + `PREPAID-BASIC`. |
| INT-004b | §9.3 Plan ineligible | Alice attempts `UNLIMITED-PREMIUM` (postpaid) | 400 `PLAN_INELIGIBLE`, `details.rule = "account_type"`; UI shows "Not eligible: account_type". | Alice (prepaid). |
| INT-005 | §9.4 Usage review | `SCR-018 UsageScreen` calls tab → `EP-050 GET /api/usage/calls` | Returns the seeded call usage record(s) for `LINE-10001`. SMS/Data/Roaming tabs render their respective lists. Date-range filter validation: `from > to` returns 400 `VALIDATION_FAILED`. | Alice + 4 seeded usage rows. |
| INT-006 | §9.5 Invoice review + PDF | `SCR-019 InvoicesScreen` → `EP-023` → `SCR-020 InvoiceDetailScreen INV-20001` → `EP-024` → Download → `EP-025` returns `application/pdf`. | Detail shows 1 line item `Unlimited Premium — monthly  39.99 EUR`. PDF body opens externally. | Bruno + `INV-20001`. |
| INT-007 | §9.6 Support ticket lifecycle | `SCR-022 SupportTicketsScreen` → FAB → `SCR-023 NewTicketScreen` → `EP-060` → `SCR-024 TicketDetailScreen` → add message via `EP-063` → Close via `EP-065` → attempt another message → `EP-063` returns 409 `TICKET_CLOSED`. | Ticket transitions `open → closed`; closed banner shown; input disabled. | Alice. |
| INT-008 | Refresh-token rotation | After INT-001, call `EP-003 POST /api/auth/refresh` with the refresh token twice in a row. | First call returns a fresh `TokenPair`; second call (token reuse) returns 401 `TOKEN_REVOKED`. | Alice. |
| INT-009 | Cross-customer 404 | Authenticated as Alice, request `GET /api/accounts/me/invoices/INV-20001` (Bruno's invoice). | 404 `NOT_FOUND` (existence not leaked). | Alice + Bruno. |
| INT-010 | Negative auth path | `EP-001` with wrong password. | 401 `INVALID_CREDENTIALS`; `LoginScreen` shows the form error. | Any seeded customer. |

## How to run

### API-only (scripts)

```bash
( cd stages/04_api_build/output/backend && uvicorn app.main:app --port 8000 ) &
bash stages/07_integration/output/scripts/smoke_api.sh
```

`smoke_api.sh` exits non-zero on any failure. Output goes to stdout. Append the result + commit SHA to [run-log.md](run-log.md).

### UI pass (emulator)

1. Start backend as above.
2. Launch Pixel 6 API 34 emulator.
3. From [stages/06_mobile_build/output/android/](../../06_mobile_build/output/android/), run `./gradlew :app:installDebug`.
4. Walk [scripts/smoke_mobile.md](scripts/smoke_mobile.md).

### `prod-like` profile (Postgres)

```bash
docker compose -f stages/07_integration/output/docker-compose.yml up --build
```

`docker-compose.yml` brings up Postgres + the backend container; backend connects via `postgresql+asyncpg://` and runs the same Alembic migration + seed. Android emulator continues to point at `10.0.2.2:8000` (Postgres-backed in this profile).

## Open questions

None. Any failure recorded in `run-log.md` traces back to its owning stage; the fix lives there, not in stage 07.
