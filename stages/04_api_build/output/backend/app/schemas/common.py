from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, condecimal

T = TypeVar("T")


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, ser_json_inf_nan="strings")


Money = Annotated[Decimal, condecimal(max_digits=12, decimal_places=2)]
UtcDatetime = Annotated[datetime, Field()]


class Page(ApiModel, Generic[T]):
    items: list[T]
    nextCursor: str | None = None


class ErrorBody(ApiModel):
    code: str
    message: str
    details: dict | None = None


class ErrorEnvelope(ApiModel):
    error: ErrorBody
