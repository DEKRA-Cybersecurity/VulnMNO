"""Tiny i18n catalog driven by `Accept-Language`. en / es supported, en is the fallback.

Loaded from `app/i18n_catalog.yaml`. Missing keys fall back to the literal key (so debug
output never crashes). Use:

    from app.i18n import translate
    translate(locale, "error.payment_declined") -> "Your card was declined."

Stage 12 keeps the application of translations narrow: error messages emitted by
`AppError` instances. Templates and JSON bodies stay English for now (admin portal is
English by design).
"""

from __future__ import annotations

import functools
import logging
from pathlib import Path
from typing import Literal

import yaml

from app.config import get_settings

log = logging.getLogger("vulnmno.i18n")

Locale = Literal["en", "es"]
DEFAULT_LOCALE: Locale = "en"
SUPPORTED: tuple[Locale, ...] = ("en", "es")


@functools.lru_cache(maxsize=1)
def _catalog() -> dict[str, dict[str, str]]:
    p = Path(get_settings().i18n_catalog_path)
    if not p.exists():
        # Built-in fallback so the app boots even if the YAML is missing.
        return {
            "en": _BUILTIN_EN,
            "es": _BUILTIN_ES,
        }
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        return {k: v for k, v in data.items() if isinstance(v, dict)}
    except Exception as exc:
        log.warning("i18n catalog %s failed to load: %s", p, exc)
        return {"en": _BUILTIN_EN, "es": _BUILTIN_ES}


def parse_locale(header: str | None) -> Locale:
    """Parse Accept-Language header. Accepts forms like 'es', 'es-ES', 'es,en;q=0.5'."""
    if not header:
        return DEFAULT_LOCALE
    primary = header.split(",")[0].split(";")[0].strip().lower()
    short = primary.split("-")[0]
    if short in SUPPORTED:
        return short  # type: ignore[return-value]
    return DEFAULT_LOCALE


def translate(locale: Locale | str, key: str, **params: object) -> str:
    locale_str = locale if locale in SUPPORTED else DEFAULT_LOCALE
    cat = _catalog().get(locale_str, _catalog().get(DEFAULT_LOCALE, {}))
    template = cat.get(key)
    if template is None:
        # Fallback to English then to the literal key.
        template = _catalog().get(DEFAULT_LOCALE, {}).get(key, key)
    try:
        return template.format(**params) if params else template
    except Exception:
        return template


# --- Built-in catalogs (used when the YAML file is missing). ---

_BUILTIN_EN = {
    "error.invalid_credentials": "Wrong phone number or password.",
    "error.otp_invalid": "OTP code is invalid or expired.",
    "error.promo_invalid": "Promo code is not valid.",
    "error.promo_ineligible": "You are not eligible for this promotion.",
    "error.insufficient_balance": "Wallet balance is too low for this purchase.",
    "error.plan_ineligible": "You are not eligible for this plan.",
    "error.payment_declined": "Your payment was declined by the gateway.",
    "error.provisioning_failed": "Service activation failed. Please contact support.",
    "error.rate_limited": "Too many requests. Please try again later.",
    "notification.purchase.title": "Purchase confirmed",
    "notification.plan_change.title": "Plan updated",
    "notification.low_balance.title": "Wallet running low",
    "notification.refund_approved.title": "Refund approved",
}

_BUILTIN_ES = {
    "error.invalid_credentials": "Número o contraseña incorrectos.",
    "error.otp_invalid": "El código OTP no es válido o ha caducado.",
    "error.promo_invalid": "El código promocional no es válido.",
    "error.promo_ineligible": "No reúnes los requisitos para esta promoción.",
    "error.insufficient_balance": "Saldo insuficiente para esta compra.",
    "error.plan_ineligible": "No puedes contratar este plan.",
    "error.payment_declined": "El pago ha sido rechazado por la pasarela.",
    "error.provisioning_failed": "Falló la activación del servicio. Contacta con soporte.",
    "error.rate_limited": "Demasiadas peticiones. Vuelve a intentarlo más tarde.",
    "notification.purchase.title": "Compra confirmada",
    "notification.plan_change.title": "Plan actualizado",
    "notification.low_balance.title": "Saldo bajo",
    "notification.refund_approved.title": "Reembolso aprobado",
}
