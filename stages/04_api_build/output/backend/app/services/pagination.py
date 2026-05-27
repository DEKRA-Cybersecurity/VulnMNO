from __future__ import annotations

import base64
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession


def encode_cursor(value: int) -> str:
    return base64.urlsafe_b64encode(str(value).encode()).decode().rstrip("=")


def decode_cursor(cursor: str | None) -> int | None:
    if not cursor:
        return None
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        return int(base64.urlsafe_b64decode(padded.encode()).decode())
    except Exception:
        return None


async def paginate(
    session: AsyncSession,
    stmt: Select,
    *,
    id_column,
    limit: int,
    cursor: str | None,
) -> tuple[list[Any], str | None]:
    after = decode_cursor(cursor)
    if after is not None:
        stmt = stmt.where(id_column < after)
    stmt = stmt.order_by(id_column.desc()).limit(limit + 1)
    rows = list((await session.execute(stmt)).scalars().all())
    if len(rows) > limit:
        nxt = rows[limit - 1]
        return rows[:limit], encode_cursor(getattr(nxt, "id"))
    return rows, None
