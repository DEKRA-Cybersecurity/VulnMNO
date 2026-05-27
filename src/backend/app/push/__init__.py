"""Push delivery adapters."""

from __future__ import annotations

from functools import lru_cache

from app.config import get_settings

from .fcm import DevPush, FcmPush, PushDelivery, SendResult

__all__ = ["PushDelivery", "SendResult", "get_push_delivery"]


@lru_cache(maxsize=1)
def get_push_delivery() -> PushDelivery:
    s = get_settings()
    if s.push_driver == "fcm":
        if not s.fcm_credentials_path:
            import logging
            logging.getLogger("vulnmno.push").warning(
                "push_driver=fcm but fcm_credentials_path is empty; falling back to dev"
            )
            return DevPush()
        try:
            return FcmPush(credentials_path=s.fcm_credentials_path)
        except Exception as exc:
            import logging
            logging.getLogger("vulnmno.push").warning("FCM init failed: %s — falling back to dev", exc)
            return DevPush()
    return DevPush()
