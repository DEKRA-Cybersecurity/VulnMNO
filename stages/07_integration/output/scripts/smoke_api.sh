#!/usr/bin/env bash
# VulnMNO backend smoke test. Exits non-zero on the first failure.
# Override BASE_URL to point elsewhere: BASE_URL=http://localhost:8000 ./smoke_api.sh
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"

red()   { printf '\033[31m%s\033[0m\n' "$*" >&2; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
ok()    { green "  ok  $*"; }
fail()  { red   "  FAIL $*"; exit 1; }
sec()   { echo; echo "== $* =="; }

j() { python3 -c "import sys,json; print(json.loads(sys.stdin.read())$1)"; }

need() { command -v "$1" >/dev/null 2>&1 || fail "missing dependency: $1"; }
need curl
need python3

# ---------- INT-001 Login (Alice, no OTP) ----------
sec "INT-001 login (Alice)"
LOGIN_BODY=$(curl -fsS -X POST "$BASE_URL/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"msisdn":"+34600000001","password":"secret123"}')
ACCESS_TOKEN=$(echo "$LOGIN_BODY" | j "['accessToken']")
REFRESH_TOKEN=$(echo "$LOGIN_BODY" | j "['refreshToken']")
[ -n "$ACCESS_TOKEN" ] || fail "no accessToken in login response"
ok "alice login → tokens"

AUTH="Authorization: Bearer $ACCESS_TOKEN"

# Home dashboard reads
for path in /api/customers/me /api/accounts/me/balance /api/plans/current "/api/shop/products?featured=true"; do
  code=$(curl -fsS -o /tmp/vulnmno_resp.json -w "%{http_code}" -H "$AUTH" "$BASE_URL$path")
  [ "$code" = "200" ] || fail "$path → $code"
  ok "$path → 200"
done

# ---------- INT-005 Usage tabs ----------
sec "INT-005 usage tabs"
for path in /api/usage/calls /api/usage/sms /api/usage/data /api/usage/roaming; do
  code=$(curl -fsS -o /dev/null -w "%{http_code}" -H "$AUTH" "$BASE_URL$path")
  [ "$code" = "200" ] || fail "$path → $code"
  ok "$path → 200"
done

# Date-range validation
code=$(curl -s -o /dev/null -w "%{http_code}" -H "$AUTH" \
  "$BASE_URL/api/usage/calls?from=2026-06-01T00:00:00Z&to=2026-05-01T00:00:00Z")
[ "$code" = "400" ] || fail "usage invalid range → $code (expected 400)"
ok "usage from>to → 400"

# ---------- INT-003 Promo + purchase ----------
sec "INT-003 promo + purchase"
PROMO=$(curl -fsS -X POST "$BASE_URL/api/shop/promotions/apply" \
  -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"productId":"DATA-10GB-7D","promoCode":"SUMMER20"}')
FINAL=$(echo "$PROMO" | j "['finalPrice']")
[ "$FINAL" = "7.99" ] || fail "promo finalPrice = $FINAL (expected 7.99)"
ok "promo SUMMER20 → finalPrice 7.99"

IDEMP=$(python3 -c 'import uuid; print(uuid.uuid4())')
PUR=$(curl -fsS -X POST "$BASE_URL/api/shop/purchases" \
  -H "$AUTH" -H 'Content-Type: application/json' -H "Idempotency-Key: $IDEMP" \
  -d '{"productId":"DATA-10GB-7D","promoCode":"SUMMER20"}')
PUR_ID=$(echo "$PUR" | j "['purchaseId']")
PUR_STATUS=$(echo "$PUR" | j "['status']")
PROV_STATUS=$(echo "$PUR" | j "['provisioning']['status']")
[ "$PUR_STATUS" = "confirmed" ] || fail "purchase status = $PUR_STATUS"
[ "$PROV_STATUS" = "active" ] || fail "provisioning status = $PROV_STATUS"
ok "purchase $PUR_ID → confirmed/active"

# Balance debited
BAL=$(curl -fsS -H "$AUTH" "$BASE_URL/api/accounts/me/balance" | j "['balance']")
ok "balance after purchase: $BAL"

# ---------- INT-009 Cross-customer 404 ----------
sec "INT-009 cross-customer 404"
code=$(curl -s -o /dev/null -w "%{http_code}" -H "$AUTH" \
  "$BASE_URL/api/accounts/me/invoices/INV-20001")
[ "$code" = "404" ] || fail "alice → invoice INV-20001 = $code (expected 404)"
ok "alice → INV-20001 → 404"

# ---------- INT-010 Wrong password ----------
sec "INT-010 invalid credentials"
RESP=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"msisdn":"+34600000001","password":"wrongwrong"}')
CODE=$(echo "$RESP" | j "['error']['code']")
[ "$CODE" = "INVALID_CREDENTIALS" ] || fail "expected INVALID_CREDENTIALS, got $CODE"
ok "wrong password → INVALID_CREDENTIALS"

# ---------- INT-007 Support ticket lifecycle ----------
sec "INT-007 ticket lifecycle"
TKT=$(curl -fsS -X POST "$BASE_URL/api/support/tickets" \
  -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"topic":"Technical","description":"Smoke ticket from script"}')
TID=$(echo "$TKT" | j "['ticketId']")
ok "ticket created: $TID"

curl -fsS -X POST "$BASE_URL/api/support/tickets/$TID/messages" \
  -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"body":"Follow up"}' >/dev/null
ok "ticket message added"

curl -fsS -X POST "$BASE_URL/api/support/tickets/$TID/close" -H "$AUTH" >/dev/null
ok "ticket closed"

CLOSED=$(curl -s -X POST "$BASE_URL/api/support/tickets/$TID/messages" \
  -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"body":"after close"}')
CLOSED_CODE=$(echo "$CLOSED" | j "['error']['code']")
[ "$CLOSED_CODE" = "TICKET_CLOSED" ] || fail "expected TICKET_CLOSED, got $CLOSED_CODE"
ok "message-after-close → TICKET_CLOSED"

# ---------- INT-004 Plan change ----------
sec "INT-004 plan change"
IDEMP=$(python3 -c 'import uuid; print(uuid.uuid4())')
PCH=$(curl -fsS -X POST "$BASE_URL/api/plans/change" \
  -H "$AUTH" -H 'Content-Type: application/json' -H "Idempotency-Key: $IDEMP" \
  -d '{"planId":"PREPAID-BASIC","mode":"immediate"}')
PCH_STATUS=$(echo "$PCH" | j "['status']")
[ "$PCH_STATUS" = "applied" ] || fail "plan change status = $PCH_STATUS"
ok "plan changed to PREPAID-BASIC → applied"

# INT-004b Plan ineligible
IDEMP=$(python3 -c 'import uuid; print(uuid.uuid4())')
RESP=$(curl -s -X POST "$BASE_URL/api/plans/change" \
  -H "$AUTH" -H 'Content-Type: application/json' -H "Idempotency-Key: $IDEMP" \
  -d '{"planId":"UNLIMITED-PREMIUM","mode":"immediate"}')
CODE=$(echo "$RESP" | j "['error']['code']")
[ "$CODE" = "PLAN_INELIGIBLE" ] || fail "expected PLAN_INELIGIBLE, got $CODE"
ok "ineligible plan → PLAN_INELIGIBLE"

# ---------- INT-008 Refresh-token rotation + reuse ----------
sec "INT-008 refresh + chain reuse"
curl -fsS -X POST "$BASE_URL/api/auth/refresh" \
  -H 'Content-Type: application/json' \
  -d "{\"refreshToken\":\"$REFRESH_TOKEN\"}" >/dev/null
ok "first refresh OK"

RESP=$(curl -s -X POST "$BASE_URL/api/auth/refresh" \
  -H 'Content-Type: application/json' \
  -d "{\"refreshToken\":\"$REFRESH_TOKEN\"}")
CODE=$(echo "$RESP" | j "['error']['code']")
[ "$CODE" = "TOKEN_REVOKED" ] || fail "expected TOKEN_REVOKED on reuse, got $CODE"
ok "refresh reuse → TOKEN_REVOKED"

# ---------- INT-002 Login + OTP (Bruno) ----------
sec "INT-002 OTP login (Bruno)"
BRUNO_LOGIN=$(curl -fsS -X POST "$BASE_URL/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"msisdn":"+34600000002","password":"secret123"}')
CHALLENGE=$(echo "$BRUNO_LOGIN" | j "['challengeToken']")
[ -n "$CHALLENGE" ] || fail "no challengeToken in OTP login"
ok "OTP challenge issued"

BRUNO_TOKENS=$(curl -fsS -X POST "$BASE_URL/api/auth/otp/verify" \
  -H 'Content-Type: application/json' \
  -d "{\"challengeToken\":\"$CHALLENGE\",\"code\":\"123456\"}")
BRUNO_ACCESS=$(echo "$BRUNO_TOKENS" | j "['accessToken']")
[ -n "$BRUNO_ACCESS" ] || fail "no accessToken after OTP verify"
ok "OTP verify → tokens"

# INT-006 Invoice + PDF (Bruno owns INV-20001)
sec "INT-006 invoice detail + PDF download"
INV=$(curl -fsS -H "Authorization: Bearer $BRUNO_ACCESS" "$BASE_URL/api/accounts/me/invoices/INV-20001")
LI_COUNT=$(echo "$INV" | python3 -c "import sys,json; print(len(json.loads(sys.stdin.read())['lineItems']))")
[ "$LI_COUNT" = "1" ] || fail "invoice line items = $LI_COUNT (expected 1)"
ok "invoice line items = 1"

CT=$(curl -fsS -o /tmp/vulnmno_inv.pdf -D - -H "Authorization: Bearer $BRUNO_ACCESS" \
  "$BASE_URL/api/accounts/me/invoices/INV-20001/download" | awk 'BEGIN{IGNORECASE=1} /^content-type:/ {print $2}' | tr -d '\r;')
echo "$CT" | grep -qi 'application/pdf' || fail "invoice download content-type = $CT"
ok "invoice download → application/pdf"

echo
green "ALL SMOKE OK ($BASE_URL)"
