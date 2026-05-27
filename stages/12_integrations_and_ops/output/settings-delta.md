# Settings delta — Phase 2

Added to `app/config.py::Settings`. All prefixed with `VULNMNO_` and read from env (or `.env` file).

## Admin portal

| Field | Type | Default | Notes |
| --- | --- | --- | --- |
| `admin_session_secret` | str | random 48-byte URL-safe | rotate to invalidate every session |
| `admin_session_max_age_seconds` | int | `8 * 3600` | sliding |
| `admin_csrf_token_bytes` | int | `32` | per-form CSRF token width |
| `seed_phase2_on_startup` | bool | `true` | seeds admin users + loyalty tiers/accounts on lifespan startup |

## Payment gateway

| Field | Type | Default | Notes |
| --- | --- | --- | --- |
| `payment_driver` | `Literal["dev", "stripe"]` | `dev` | dev keeps Phase-1 behavior |
| `stripe_secret_key` | str | "" | required if driver=stripe; empty key degrades to dev with warning |
| `stripe_base_url` | str | `https://api.stripe.com` | swap for sandbox or mock |

## Provisioning

| Field | Type | Default | Notes |
| --- | --- | --- | --- |
| `provisioning_driver` | `Literal["dev", "http"]` | `dev` | |
| `provisioning_url` | str | "" | required if driver=http |

## Push delivery

| Field | Type | Default | Notes |
| --- | --- | --- | --- |
| `push_driver` | `Literal["dev", "fcm"]` | `dev` | |
| `fcm_credentials_path` | str | "" | path to a service-account JSON; empty degrades to dev |

## Rate limiting + i18n

| Field | Type | Default | Notes |
| --- | --- | --- | --- |
| `rate_limit_enabled` | bool | `true` | toggle slowapi middleware |
| `default_locale` | `Literal["en", "es"]` | `en` | fallback when `Accept-Language` is missing or unsupported |
| `i18n_catalog_path` | Path | `./app/i18n_catalog.yaml` | YAML catalog file location |

## Campaign scheduler

| Field | Type | Default | Notes |
| --- | --- | --- | --- |
| `campaign_scheduler_interval_seconds` | int | `3600` | sweep frequency for auto-open / auto-close of promotions |

## Example dev `.env`

```
VULNMNO_ENV=dev
VULNMNO_DATABASE_URL=sqlite+aiosqlite:///./dev.db
VULNMNO_PAYMENT_DRIVER=dev
VULNMNO_PROVISIONING_DRIVER=dev
VULNMNO_PUSH_DRIVER=dev
VULNMNO_RATE_LIMIT_ENABLED=true
VULNMNO_DEFAULT_LOCALE=en
```

## Example prod-like `.env`

```
VULNMNO_ENV=prod-like
VULNMNO_DATABASE_URL=postgresql+asyncpg://vulnmno:vulnmno@db:5432/vulnmno
VULNMNO_ADMIN_SESSION_SECRET=<48-byte secret>
VULNMNO_PAYMENT_DRIVER=stripe
VULNMNO_STRIPE_SECRET_KEY=sk_test_...
VULNMNO_PROVISIONING_DRIVER=http
VULNMNO_PROVISIONING_URL=http://provisioning-mock:9000
VULNMNO_PUSH_DRIVER=fcm
VULNMNO_FCM_CREDENTIALS_PATH=/run/secrets/fcm-service-account.json
```
