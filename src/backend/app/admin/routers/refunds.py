from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_session
from app.errors import AppError, ErrorCode, conflict, not_found
from app.models import AdminUser, Refund

from ..deps import get_current_admin, require_csrf, require_module
from ..permissions import Access, Module
from ..templates_loader import render

router = APIRouter(prefix="/admin/refunds")


@router.get("")
async def refunds_list(
    request: Request,
    admin: Annotated[AdminUser, Depends(require_module(Module.REFUND_WORKFLOW, Access.READ))],
    session: Annotated[AsyncSession, Depends(get_session)],
    status_filter: str | None = "pending",
):
    stmt = select(Refund)
    if status_filter:
        stmt = stmt.where(Refund.status == status_filter)
    refunds = (await session.execute(stmt.order_by(Refund.id.desc()).limit(50))).scalars().all()
    can_act = admin.role in ("billing_operator", "ops_admin")
    return render(request, "admin/refunds/list.html",
                  {"refunds": refunds, "status_filter": status_filter, "can_act": can_act})


@router.post("/{refundId}/approve")
async def refund_approve(
    request: Request,
    refundId: str,
    admin: Annotated[AdminUser, Depends(require_module(Module.REFUND_WORKFLOW, Access.READ_WRITE))],
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, Depends(require_csrf)],
    note: Annotated[str, Form()] = "",
    auto_close: Annotated[bool, Form()] = True,
):
    refund = (
        await session.execute(select(Refund).where(Refund.public_id == refundId))
    ).scalar_one_or_none()
    if refund is None:
        raise not_found("Refund not found")
    if refund.status != "pending":
        raise conflict(ErrorCode.CONFLICT, "Refund not in pending state")

    refund.status = "approved"
    # Phase 2 — credit the customer's wallet via the refund service.
    from app.services.refund import credit_wallet_for_refund
    await credit_wallet_for_refund(session, refund=refund)

    from app.models import TicketMessage
    if refund.ticket_id is not None:
        session.add(TicketMessage(
            public_id=f"MSG-AUTO-{refund.id}",
            ticket_id=refund.ticket_id,
            author_role="system",
            author_display_name=f"Refund workflow (approved by {admin.full_name})",
            body=note or f"Refund {refundId} approved.",
        ))
        if auto_close:
            from app.models import SupportTicket
            ticket = (
                await session.execute(select(SupportTicket).where(SupportTicket.id == refund.ticket_id))
            ).scalar_one_or_none()
            if ticket is not None and ticket.status != "closed":
                ticket.status = "closed"

    from ..services.audit import write_admin_audit
    await write_admin_audit(
        session, admin=admin, event_type="ADMIN_REFUND_APPROVED",
        target_type="refund", target_id=refundId,
        payload={"note": note, "auto_close": auto_close}, request=request,
    )
    return RedirectResponse(url="/admin/refunds", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{refundId}/quick-approve")
async def refund_quick_approve(
    request: Request,
    refundId: str,
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, Depends(require_csrf)],
):
    """API5 training lab (OWASP API Security Top 10) — see
    src/docs/vulns/api/API5-Broken-Function-Level-Authorization.md.
    Copy-pasted from refund_approve but gated by get_current_admin (any
    logged-in admin session) instead of
    require_module(Module.REFUND_WORKFLOW, Access.READ_WRITE) — no
    role/module check at all."""
    refund = (
        await session.execute(select(Refund).where(Refund.public_id == refundId))
    ).scalar_one_or_none()
    if refund is None:
        raise not_found("Refund not found")
    if refund.status != "pending":
        raise conflict(ErrorCode.CONFLICT, "Refund not in pending state")

    refund.status = "approved"
    from app.services.refund import credit_wallet_for_refund
    await credit_wallet_for_refund(session, refund=refund)

    from ..services.audit import write_admin_audit
    await write_admin_audit(
        session, admin=admin, event_type="ADMIN_REFUND_APPROVED",
        target_type="refund", target_id=refundId,
        payload={"via": "quick-approve"}, request=request,
    )
    return RedirectResponse(url="/admin/refunds", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{refundId}/reject")
async def refund_reject(
    request: Request,
    refundId: str,
    reason: Annotated[str, Form()],
    admin: Annotated[AdminUser, Depends(require_module(Module.REFUND_WORKFLOW, Access.READ_WRITE))],
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, Depends(require_csrf)],
):
    if len(reason) < 5:
        raise AppError(ErrorCode.VALIDATION_FAILED, "Reason must be ≥ 5 chars", http_status=400)
    refund = (
        await session.execute(select(Refund).where(Refund.public_id == refundId))
    ).scalar_one_or_none()
    if refund is None:
        raise not_found("Refund not found")
    if refund.status != "pending":
        raise conflict(ErrorCode.CONFLICT, "Refund not in pending state")
    refund.status = "rejected"

    from app.models import TicketMessage
    if refund.ticket_id is not None:
        session.add(TicketMessage(
            public_id=f"MSG-AUTO-R{refund.id}",
            ticket_id=refund.ticket_id,
            author_role="system",
            author_display_name=f"Refund workflow (rejected by {admin.full_name})",
            body=reason,
        ))

    from ..services.audit import write_admin_audit
    await write_admin_audit(
        session, admin=admin, event_type="ADMIN_REFUND_REJECTED",
        target_type="refund", target_id=refundId, payload={"reason": reason}, request=request,
    )
    return RedirectResponse(url="/admin/refunds", status_code=status.HTTP_303_SEE_OTHER)
