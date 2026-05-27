"""Push delivery — dev (log only) + FCM (firebase-admin SDK).

firebase-admin is an optional dependency. The FcmPush driver lazy-imports it; if missing,
construction raises ImportError which the factory catches and downgrades to DevPush.
"""

from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from typing import Literal, Protocol

log = logging.getLogger("vulnmno.push")

PushErrorCode = Literal["ok", "no_token", "invalid_token", "rate_limited", "provider_error"]


@dataclass(frozen=True)
class SendResult:
    success: bool
    provider_message_id: str | None
    error_code: PushErrorCode
    error_message: str | None = None


class PushDelivery(Protocol):
    name: str

    async def send(
        self,
        *,
        customer_id: str,
        notification_id: str,
        title: str,
        body: str,
        data: dict[str, str],
    ) -> SendResult: ...


class DevPush:
    name = "dev"

    async def send(
        self, *, customer_id: str, notification_id: str, title: str, body: str, data: dict[str, str],
    ) -> SendResult:
        log.info(
            "DEV PUSH customer=%s notification=%s title=%r data=%s",
            customer_id, notification_id, title, data,
        )
        return SendResult(
            success=True,
            provider_message_id=f"dev_{secrets.token_hex(8)}",
            error_code="ok",
        )


class FcmPush:
    name = "fcm"

    def __init__(self, *, credentials_path: str) -> None:
        # Lazy-import to keep firebase-admin optional.
        from firebase_admin import credentials, initialize_app, get_app  # type: ignore

        try:
            self._app = get_app("vulnmno-fcm")
        except ValueError:
            cred = credentials.Certificate(credentials_path)
            self._app = initialize_app(cred, name="vulnmno-fcm")

    async def send(
        self, *, customer_id: str, notification_id: str, title: str, body: str, data: dict[str, str],
    ) -> SendResult:
        # We need the device token for this customer; the audit_hook layer is responsible
        # for resolving customer_id → device token rows. To keep this driver storage-agnostic,
        # we let the caller pass the token in `data["__token"]`. If missing, no-token.
        token = data.pop("__token", None)
        if not token:
            return SendResult(False, None, "no_token", "Customer has no registered device token")

        try:
            import asyncio

            from firebase_admin import messaging  # type: ignore

            def _send() -> str:
                msg = messaging.Message(
                    notification=messaging.Notification(title=title, body=body),
                    data=data or {},
                    token=token,
                )
                return messaging.send(msg, app=self._app)

            msg_id = await asyncio.to_thread(_send)
            return SendResult(True, msg_id, "ok")
        except Exception as exc:  # firebase_admin exceptions are noisy; trap broadly here
            cls = type(exc).__name__
            if "UnregisteredError" in cls or "InvalidArgument" in cls:
                return SendResult(False, None, "invalid_token", str(exc))
            return SendResult(False, None, "provider_error", f"{cls}: {exc}")
