"""External integration adapters.

Each gateway has a Protocol interface (PEP 544) + a `dev` driver (preserves Phase 1
behavior, no external calls) + an optional real driver. Driver selection happens at
import time via `get_payment_gateway()` / `get_provisioning_client()` which read
the env-bound Settings instance.
"""

from __future__ import annotations

from functools import lru_cache

from app.config import get_settings

from .payment import DevPaymentGateway, PaymentGateway, StripePaymentGateway
from .provisioning import DevProvisioning, HttpProvisioning, ProvisioningClient

__all__ = [
    "PaymentGateway",
    "ProvisioningClient",
    "get_payment_gateway",
    "get_provisioning_client",
]


@lru_cache(maxsize=1)
def get_payment_gateway() -> PaymentGateway:
    s = get_settings()
    if s.payment_driver == "stripe":
        if not s.stripe_secret_key:
            # Misconfigured — fall back to dev with a warning instead of crashing on import.
            import logging
            logging.getLogger("vulnmno.gateways").warning(
                "payment_driver=stripe but stripe_secret_key is empty; falling back to dev"
            )
            return DevPaymentGateway()
        return StripePaymentGateway(secret_key=s.stripe_secret_key, base_url=s.stripe_base_url)
    return DevPaymentGateway()


@lru_cache(maxsize=1)
def get_provisioning_client() -> ProvisioningClient:
    s = get_settings()
    if s.provisioning_driver == "http":
        if not s.provisioning_url:
            import logging
            logging.getLogger("vulnmno.gateways").warning(
                "provisioning_driver=http but provisioning_url is empty; falling back to dev"
            )
            return DevProvisioning()
        return HttpProvisioning(base_url=s.provisioning_url)
    return DevProvisioning()
