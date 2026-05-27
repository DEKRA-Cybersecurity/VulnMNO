"""Provisioning client adapters — dev (instant) + http (calls a mock provisioning service)."""

from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from typing import Literal, Protocol

import httpx

log = logging.getLogger("vulnmno.gateways.provisioning")

ProvisionErrorCode = Literal["ok", "transient", "permanent", "timeout"]


@dataclass(frozen=True)
class ProvisionResult:
    success: bool
    provisioning_id: str | None
    raw_status: str
    error_code: ProvisionErrorCode
    error_message: str | None = None


class ProvisioningClient(Protocol):
    name: str

    async def activate_bundle(
        self, *, customer_id: str, product_id: str, purchase_id: str
    ) -> ProvisionResult: ...


class DevProvisioning:
    name = "dev"

    async def activate_bundle(self, **kwargs) -> ProvisionResult:
        return ProvisionResult(
            success=True,
            provisioning_id=f"dev_{secrets.token_hex(8)}",
            raw_status="active",
            error_code="ok",
        )


class HttpProvisioning:
    name = "http"

    def __init__(self, *, base_url: str) -> None:
        self._base = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=10.0)

    async def activate_bundle(
        self, *, customer_id: str, product_id: str, purchase_id: str
    ) -> ProvisionResult:
        try:
            r = await self._client.post(
                f"{self._base}/activate",
                json={"customerId": customer_id, "productId": product_id, "purchaseId": purchase_id},
            )
        except httpx.HTTPError as exc:
            return ProvisionResult(False, None, "timeout", "transient", str(exc))
        if r.status_code in (200, 201, 202):
            data = r.json()
            return ProvisionResult(
                success=True,
                provisioning_id=data.get("provisioningId"),
                raw_status=data.get("status", "active"),
                error_code="ok",
            )
        # 4xx is permanent, 5xx transient
        code: ProvisionErrorCode = "permanent" if 400 <= r.status_code < 500 else "transient"
        return ProvisionResult(
            success=False, provisioning_id=None,
            raw_status=str(r.status_code), error_code=code,
            error_message=r.text[:200],
        )
