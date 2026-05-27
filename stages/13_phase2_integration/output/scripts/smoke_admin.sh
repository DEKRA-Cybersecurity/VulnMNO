#!/usr/bin/env bash
# VulnMNO admin portal + Phase 2 smoke. Exits non-zero on the first failure.
#   BASE_URL=http://localhost:8000 ./smoke_admin.sh
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
JAR=$(mktemp)
trap 'rm -f "$JAR"' EXIT

red()   { printf '\033[31m%s\033[0m\n' "$*" >&2; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
ok()    { green "  ok  $*"; }
fail()  { red   "  FAIL $*"; exit 1; }
sec()   { echo; echo "== $* =="; }

j() { python3 -c "import sys,json; print(json.loads(sys.stdin.read())$1)"; }

need() { command -v "$1" >/dev/null 2>&1 || fail "missing dependency: $1"; }
need curl
need python3

# ---------- helpers ----------
extract_csrf() {
  # Reads a full HTML page from stdin, extracts the first csrf_token input value.
  # Implemented as a one-liner — using `python3 - <<EOF` would shadow our piped HTML
  # because the heredoc itself occupies python's stdin.
  python3 -c 'import sys,re; m=re.search(r"name=\"csrf_token\"\s+value=\"([^\"]+)\"", sys.stdin.read()); print(m.group(1) if m else "")'
}

admin_login() {
  local user="$1"
  local pass="$2"
  rm -f "$JAR"
  HTML=$(curl -fsS -c "$JAR" "$BASE_URL/admin/login")
  CSRF=$(printf '%s' "$HTML" | extract_csrf)
  [ -n "$CSRF" ] || fail "no csrf on /admin/login"
  curl -fsS -b "$JAR" -c "$JAR" -X POST -o /dev/null \
    -d "username=${user}&password=${pass}&csrf_token=${CSRF}&next=/admin/" \
    "$BASE_URL/admin/login"
  # After login the CSRF rotates — fetch the dashboard to pick up the new one.
  HTML=$(curl -fsS -b "$JAR" "$BASE_URL/admin/")
  printf '%s' "$HTML" | extract_csrf
}

# ---------- INT-200 admin login ----------
sec "INT-200 admin login as ops"
CSRF=$(admin_login "ops" "admin1234")
[ -n "$CSRF" ] || fail "post-login dashboard returned no CSRF"
ok "ops logged in, dashboard CSRF rotated"

# ---------- INT-201 admin balance adjust (billing role) ----------
sec "INT-201 balance adjust as billing"
CSRF=$(admin_login "billing" "admin1234")
RESP=$(curl -fsS -b "$JAR" -X POST "$BASE_URL/admin/customers/CUST-10001/balance-adjust" \
  -d "amount=5.00&reason=Smoke%20adjustment%20test&csrf_token=${CSRF}")
echo "$RESP" | grep -q "Balance updated" || fail "balance card did not refresh"
ok "balance adjust returned updated card"

# ---------- INT-202 RBAC denial (support_agent) ----------
sec "INT-202 RBAC: support_agent CANNOT adjust balance"
CSRF=$(admin_login "support" "admin1234")
STATUS=$(curl -s -b "$JAR" -o /tmp/vulnmno_resp -w "%{http_code}" -X POST \
  "$BASE_URL/admin/customers/CUST-10001/balance-adjust" \
  -d "amount=1.00&reason=Should%20be%20forbidden&csrf_token=${CSRF}")
[ "$STATUS" = "403" ] || fail "support_agent → expected 403, got $STATUS"
grep -q "ADMIN_FORBIDDEN" /tmp/vulnmno_resp || fail "expected ADMIN_FORBIDDEN in body"
ok "support_agent → 403 ADMIN_FORBIDDEN"

# ---------- INT-207 / INT-208 loyalty ----------
sec "INT-207 loyalty accrues on purchase"
LOGIN_BODY=$(curl -fsS -X POST "$BASE_URL/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"msisdn":"+34600000001","password":"secret123"}')
TOKEN=$(echo "$LOGIN_BODY" | j "['accessToken']")
AUTH="Authorization: Bearer $TOKEN"

LA_BEFORE=$(curl -fsS -H "$AUTH" "$BASE_URL/api/loyalty/account")
PTS_BEFORE=$(echo "$LA_BEFORE" | j "['points']")
ok "loyalty before: $PTS_BEFORE pts"

IDEMP=$(python3 -c 'import uuid; print(uuid.uuid4())')
curl -fsS -X POST "$BASE_URL/api/shop/purchases" \
  -H "$AUTH" -H 'Content-Type: application/json' -H "Idempotency-Key: $IDEMP" \
  -d '{"productId":"DATA-10GB-7D","promoCode":"SUMMER20"}' >/dev/null

LA_AFTER=$(curl -fsS -H "$AUTH" "$BASE_URL/api/loyalty/account")
PTS_AFTER=$(echo "$LA_AFTER" | j "['points']")
TIER_AFTER=$(echo "$LA_AFTER" | j "['tier']")
[ "$PTS_AFTER" -gt "$PTS_BEFORE" ] || fail "loyalty points did not increase"
[ "$TIER_AFTER" = "silver" ] || fail "tier downgraded unexpectedly to $TIER_AFTER"
ok "loyalty after: $PTS_AFTER pts tier=$TIER_AFTER"

sec "INT-208 loyalty transaction logged"
LTX=$(curl -fsS -H "$AUTH" "$BASE_URL/api/loyalty/transactions" | j "['items'][0]")
echo "$LTX" | grep -q "purchase" || fail "no purchase-reason loyalty transaction"
ok "loyalty transaction row present"

# ---------- INT-209 / INT-210 i18n ----------
sec "INT-209/210 i18n error messages"
RESP_ES=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H 'Content-Type: application/json' -H 'Accept-Language: es' \
  -d '{"msisdn":"+34600000001","password":"wrongwrong"}')
MSG_ES=$(echo "$RESP_ES" | j "['error']['message']")
echo "$MSG_ES" | grep -qi "incorrecto" || fail "es message wrong: $MSG_ES"
ok "es: $MSG_ES"

RESP_EN=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H 'Content-Type: application/json' -H 'Accept-Language: en' \
  -d '{"msisdn":"+34600000001","password":"wrongwrong"}')
MSG_EN=$(echo "$RESP_EN" | j "['error']['message']")
echo "$MSG_EN" | grep -qi "wrong" || fail "en message wrong: $MSG_EN"
ok "en: $MSG_EN"

# ---------- INT-211 rate limit ----------
sec "INT-211 rate limit triggers 429"
SAW_429=0
for _ in $(seq 1 7); do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/auth/login" \
    -H 'Content-Type: application/json' \
    -d '{"msisdn":"+34600009999","password":"wrongwrong"}')
  if [ "$CODE" = "429" ]; then SAW_429=1; break; fi
done
[ "$SAW_429" = "1" ] || fail "no 429 observed across 7 attempts (rate limit not enforced?)"
ok "rate limit reached 429"

echo
green "ALL PHASE 2 ADMIN SMOKE OK ($BASE_URL)"
