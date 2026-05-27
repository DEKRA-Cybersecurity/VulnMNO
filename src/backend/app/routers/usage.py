from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_customer, get_session
from app.errors import ErrorCode, bad_request
from app.models import Customer, MobileLine, UsageRecord
from app.schemas.common import Page
from app.schemas.usage import UsageRecordRead
from app.services.pagination import paginate

router = APIRouter(prefix="/api/usage", tags=["usage"])


async def _line_ids(session: AsyncSession, customer: Customer) -> list[int]:
    rows = (
        await session.execute(
            select(MobileLine.id).where(MobileLine.customer_id == customer.id)
        )
    ).scalars().all()
    return list(rows)


def _validate_range(from_: datetime | None, to: datetime | None) -> None:
    if from_ and to and from_ > to:
        raise bad_request(ErrorCode.VALIDATION_FAILED, "from > to")


def _to_read(u: UsageRecord, line_public_id: str) -> UsageRecordRead:
    return UsageRecordRead(
        usageId=u.public_id,
        lineId=line_public_id,
        type=u.type,
        direction=u.direction,
        destination=u.destination,
        startedAt=u.started_at,
        durationSeconds=u.duration_seconds,
        volumeMegabytes=u.volume_megabytes,
        country=u.country,
        networkType=u.network_type,
        roaming=u.roaming,
        cost=u.cost,
        currency=u.currency,
    )


async def _list_by_type(
    session: AsyncSession,
    customer: Customer,
    type_filter: str,
    from_: datetime | None,
    to: datetime | None,
    limit: int,
    cursor: str | None,
) -> Page[UsageRecordRead]:
    _validate_range(from_, to)
    line_ids = await _line_ids(session, customer)
    if not line_ids:
        return Page(items=[], nextCursor=None)
    stmt = select(UsageRecord).where(
        UsageRecord.line_id.in_(line_ids), UsageRecord.type == type_filter
    )
    if from_:
        stmt = stmt.where(UsageRecord.started_at >= from_)
    if to:
        stmt = stmt.where(UsageRecord.started_at <= to)
    rows, nxt = await paginate(session, stmt, id_column=UsageRecord.id, limit=limit, cursor=cursor)
    # Pre-fetch public ids for the lines used
    line_map = {
        row.id: row.public_id
        for row in (
            await session.execute(select(MobileLine).where(MobileLine.id.in_(line_ids)))
        ).scalars().all()
    }
    return Page(
        items=[_to_read(u, line_map[u.line_id]) for u in rows],
        nextCursor=nxt,
    )


@router.get("/calls", response_model=Page[UsageRecordRead])
async def usage_calls(
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = None,
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = None,
):
    return await _list_by_type(session, customer, "call", from_, to, limit, cursor)


@router.get("/sms", response_model=Page[UsageRecordRead])
async def usage_sms(
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = None,
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = None,
):
    return await _list_by_type(session, customer, "sms", from_, to, limit, cursor)


@router.get("/data", response_model=Page[UsageRecordRead])
async def usage_data(
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = None,
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = None,
):
    return await _list_by_type(session, customer, "data", from_, to, limit, cursor)


@router.get("/roaming", response_model=Page[UsageRecordRead])
async def usage_roaming(
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = None,
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = None,
):
    return await _list_by_type(session, customer, "roaming", from_, to, limit, cursor)


@router.get("/export")
async def export_usage(
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
    format: Literal["csv", "json"] = Query(...),
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = None,
):
    _validate_range(from_, to)
    line_ids = await _line_ids(session, customer)
    stmt = select(UsageRecord).where(UsageRecord.line_id.in_(line_ids))
    if from_:
        stmt = stmt.where(UsageRecord.started_at >= from_)
    if to:
        stmt = stmt.where(UsageRecord.started_at <= to)
    rows = (await session.execute(stmt.order_by(UsageRecord.started_at))).scalars().all()
    line_map = {
        row.id: row.public_id
        for row in (
            await session.execute(select(MobileLine).where(MobileLine.id.in_(line_ids)))
        ).scalars().all()
    }
    items = [_to_read(u, line_map[u.line_id]) for u in rows]
    if format == "json":
        return JSONResponse([i.model_dump(mode="json") for i in items])
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "usageId", "lineId", "type", "direction", "destination",
        "startedAt", "durationSeconds", "volumeMegabytes", "cost", "currency",
    ])
    for u in items:
        writer.writerow([
            u.usageId, u.lineId, u.type, u.direction or "", u.destination or "",
            u.startedAt.isoformat(), u.durationSeconds or "", u.volumeMegabytes or "",
            u.cost, u.currency,
        ])
    return StreamingResponse(io.BytesIO(buf.getvalue().encode()), media_type="text/csv")
