from __future__ import annotations

from typing import Literal, Union

from pydantic import Field

from .common import ApiModel


class LoginRequest(ApiModel):
    msisdn: str = Field(pattern=r"^\+[0-9]{8,15}$")
    password: str = Field(min_length=8, max_length=128)


class TokenPair(ApiModel):
    accessToken: str
    refreshToken: str
    expiresIn: int
    tokenType: Literal["Bearer"] = "Bearer"


class OtpChallenge(ApiModel):
    challenge: Literal["OTP"] = "OTP"
    challengeToken: str
    expiresIn: int


LoginResponse = Union[TokenPair, OtpChallenge]


class RefreshRequest(ApiModel):
    refreshToken: str


class OtpVerifyRequest(ApiModel):
    challengeToken: str
    code: str = Field(pattern=r"^[0-9]{6}$")


class PasswordResetRequest(ApiModel):
    msisdn: str = Field(pattern=r"^\+[0-9]{8,15}$")


class PasswordResetConfirm(ApiModel):
    msisdn: str = Field(pattern=r"^\+[0-9]{8,15}$")
    code: str = Field(pattern=r"^[0-9]{6}$")
    newPassword: str = Field(min_length=8, max_length=128)


class DeviceRegisterRequest(ApiModel):
    deviceId: str = Field(min_length=4, max_length=128)
    platform: Literal["android", "ios", "web"] = "android"
    model: str | None = Field(default=None, max_length=120)
    appVersion: str | None = Field(default=None, max_length=40)
    # API7 training lab (OWASP API Security Top 10) — see
    # src/docs/vulns/api/API7-Server-Side-Request-Forgery.md.
    callbackUrl: str | None = Field(default=None, max_length=2048)


class DeviceRegisterResult(ApiModel):
    deviceId: str
    recognized: bool
    registeredAt: str
