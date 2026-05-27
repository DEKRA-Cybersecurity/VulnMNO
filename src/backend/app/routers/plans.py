from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import IdempotencyKey, get_current_customer, get_session
from app.errors import AppError, ErrorCode, bad_request, conflict, not_found
from app.ids import next_plan_change_id
from app.models import (
    Customer,
    CustomerService,
    MobileLine,
    Plan,
    PlanChange,
)
from app.schemas.common import Page
from app.schemas.plan import (
    PlanChangeRead,
    PlanChangeRequest,
    PlanRead,
    ServiceToggleRequest,
)
from app.services.audit import write_audit
from app.security import now

router = APIRouter(prefix="/api/plans", tags=["plans"])


def _plan_read(p: Plan, active_services: list[str]) -> PlanRead:
    return PlanRead(
        planId=p.public_id,
        name=p.name,
        description=p.description,
        monthlyPrice=p.monthly_price,
        currency=p.currency,
        dataLimit=p.data_limit_mb,
        voiceLimit=p.voice_limit_min,
        smsLimit=p.sms_limit,
        category=p.category,
        activeServices=active_services,
    )


async def _customer_line(session: AsyncSession, customer: Customer) -> MobileLine:
    line = (
        await session.execute(
            select(MobileLine).where(
                MobileLine.customer_id == customer.id, MobileLine.deleted_at.is_(None)
            )
        )
    ).scalars().first()
    if line is None:
        raise not_found("No active mobile line for this customer")
    return line


async def _active_services(session: AsyncSession, customer: Customer) -> list[str]:
    rows = (
        await session.execute(
            select(CustomerService.service_id).where(CustomerService.customer_id == customer.id)
        )
    ).scalars().all()
    return list(rows)


def _eligible_for_plan(customer: Customer, plan: Plan) -> tuple[bool, str | None]:
    rules = plan.eligibility_rules or {}
    if plan.category == "postpaid" and customer.account_type == "prepaid":
        return False, "account_type"
    if "min_loyalty_tier" in rules:
        order = {"bronze": 0, "silver": 1, "gold": 2, "platinum": 3}
        if order.get(customer.loyalty_tier, 0) < order.get(rules["min_loyalty_tier"], 0):
            return False, "loyalty_tier"
    return True, None


@router.get("/current", response_model=PlanRead)
async def get_current_plan(
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    line = await _customer_line(session, customer)
    if line.plan_id is None:
        raise not_found("Customer has no active plan")
    plan = (await session.execute(select(Plan).where(Plan.id == line.plan_id))).scalar_one()
    return _plan_read(plan, await _active_services(session, customer))


@router.get("/available", response_model=Page[PlanRead])
async def list_available_plans(
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(20, ge=1, le=100),
):
    plans = (await session.execute(select(Plan))).scalars().all()
    visible = [p for p in plans if _eligible_for_plan(customer, p)[0]]
    services = await _active_services(session, customer)
    return Page(items=[_plan_read(p, services) for p in visible[:limit]], nextCursor=None)


@router.post("/change", response_model=PlanChangeRead)
async def change_plan(
    body: PlanChangeRequest,
    response: Response,
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
    idempotency_key: IdempotencyKey = None,
):
    target = (
        await session.execute(select(Plan).where(Plan.public_id == body.planId))
    ).scalar_one_or_none()
    if target is None:
        raise not_found("Plan not found")
    ok, rule = _eligible_for_plan(customer, target)
    if not ok:
        raise bad_request(ErrorCode.PLAN_INELIGIBLE, "Plan ineligible", rule=rule)

    pending = (
        await session.execute(
            select(PlanChange).where(
                PlanChange.customer_id == customer.id, PlanChange.status == "pending"
            )
        )
    ).scalars().first()
    if pending is not None:
        raise conflict(ErrorCode.PLAN_CHANGE_PENDING, "A pending plan change exists")

    line = await _customer_line(session, customer)
    from_plan_id = line.plan_id

    change = PlanChange(
        public_id=await next_plan_change_id(session),
        customer_id=customer.id,
        from_plan_id=from_plan_id,
        to_plan_id=target.id,
        mode=body.mode,
        status="applied" if body.mode == "immediate" else "pending",
        effective_date=body.effectiveDate,
        applied_at=now() if body.mode == "immediate" else None,
    )
    session.add(change)
    await session.flush()

    if body.mode == "immediate":
        line.plan_id = target.id
        response.status_code = status.HTTP_200_OK
    else:
        response.status_code = status.HTTP_202_ACCEPTED

    await write_audit(
        session,
        event_type="PLAN_CHANGE",
        actor_id=customer.public_id,
        target_type="plan",
        target_id=target.public_id,
        payload={"mode": body.mode, "changeId": change.public_id},
    )

    from_public = None
    if from_plan_id is not None:
        fp = (await session.execute(select(Plan).where(Plan.id == from_plan_id))).scalar_one()
        from_public = fp.public_id
    return PlanChangeRead(
        changeId=change.public_id,
        customerId=customer.public_id,
        fromPlanId=from_public,
        toPlanId=target.public_id,
        status=change.status,
        mode=change.mode,
        effectiveDate=change.effective_date,
        createdAt=change.created_at,
    )


@router.post("/change/{changeId}/cancel", response_model=PlanChangeRead)
async def cancel_plan_change(
    changeId: str,
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    change = (
        await session.execute(
            select(PlanChange).where(
                PlanChange.public_id == changeId, PlanChange.customer_id == customer.id
            )
        )
    ).scalar_one_or_none()
    if change is None:
        raise not_found("Plan change not found")
    if change.status != "pending":
        raise conflict(ErrorCode.CONFLICT, "Plan change no longer cancellable")
    change.status = "cancelled"
    from_public = None
    if change.from_plan_id is not None:
        fp = (await session.execute(select(Plan).where(Plan.id == change.from_plan_id))).scalar_one()
        from_public = fp.public_id
    target = (await session.execute(select(Plan).where(Plan.id == change.to_plan_id))).scalar_one()
    return PlanChangeRead(
        changeId=change.public_id,
        customerId=customer.public_id,
        fromPlanId=from_public,
        toPlanId=target.public_id,
        status=change.status,
        mode=change.mode,
        effectiveDate=change.effective_date,
        createdAt=change.created_at,
    )


@router.post("/services/add", response_model=PlanRead)
async def add_service(
    body: ServiceToggleRequest,
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    line = await _customer_line(session, customer)
    plan = (await session.execute(select(Plan).where(Plan.id == line.plan_id))).scalar_one()
    if body.serviceId not in (plan.available_services or []):
        raise conflict(ErrorCode.CONFLICT, "Service not available on current plan")
    existing = (
        await session.execute(
            select(CustomerService).where(
                CustomerService.customer_id == customer.id,
                CustomerService.service_id == body.serviceId,
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        session.add(CustomerService(customer_id=customer.id, service_id=body.serviceId))
        await session.flush()
    return _plan_read(plan, await _active_services(session, customer))


@router.post("/services/remove", response_model=PlanRead)
async def remove_service(
    body: ServiceToggleRequest,
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    line = await _customer_line(session, customer)
    plan = (await session.execute(select(Plan).where(Plan.id == line.plan_id))).scalar_one()
    existing = (
        await session.execute(
            select(CustomerService).where(
                CustomerService.customer_id == customer.id,
                CustomerService.service_id == body.serviceId,
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        raise conflict(ErrorCode.CONFLICT, "Service not active")
    await session.delete(existing)
    await session.flush()
    return _plan_read(plan, await _active_services(session, customer))
