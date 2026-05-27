from __future__ import annotations

import secrets
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.deps import get_current_customer, get_session
from app.errors import not_found
from app.ids import next_sim_id
from app.models import Customer, MobileLine, SIMProfile
from app.schemas.common import Page
from app.schemas.customer import (
    ContactDetailsUpdate,
    CustomerRead,
    MobileLineRead,
    SimProfileRead,
    SimSwapRequest,
    SimSwapResult,
)
from app.services.audit import write_audit

router = APIRouter(prefix="/api/customers", tags=["customers"])


def _to_customer(c: Customer) -> CustomerRead:
    return CustomerRead(
        customerId=c.public_id,
        name=c.name,
        email=c.email,
        primaryMsisdn=c.primary_msisdn,
        accountType=c.account_type,
        status=c.status,
        loyaltyTier=c.loyalty_tier,
        billingAddress=c.billing_address,
        notificationPreferences=c.notification_preferences,
    )


@router.get("/me", response_model=CustomerRead)
async def get_me(customer: Annotated[Customer, Depends(get_current_customer)]):
    return _to_customer(customer)


@router.put("/me/contact-details", response_model=CustomerRead)
async def update_contact_details(
    body: ContactDetailsUpdate,
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    if body.email is not None:
        customer.email = body.email
    if body.billingAddress is not None:
        customer.billing_address = body.billingAddress.model_dump(exclude_none=True)
    if body.notificationPreferences is not None:
        prefs = dict(customer.notification_preferences or {})
        for k, v in body.notificationPreferences.model_dump(exclude_none=True).items():
            prefs[k] = v
        customer.notification_preferences = prefs
    await session.flush()
    return _to_customer(customer)


@router.get("/me/lines", response_model=Page[MobileLineRead])
async def list_lines(
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(20, ge=1, le=100),
):
    rows = (
        await session.execute(
            select(MobileLine)
            .where(MobileLine.customer_id == customer.id, MobileLine.deleted_at.is_(None))
            .options(selectinload(MobileLine.plan), selectinload(MobileLine.sim))
        )
    ).scalars().all()
    items = [
        MobileLineRead(
            lineId=ln.public_id,
            msisdn=ln.msisdn,
            customerId=customer.public_id,
            planId=ln.plan.public_id if ln.plan else None,
            simId=ln.sim.public_id if ln.sim else None,
            status=ln.status,
            activatedAt=ln.activated_at,
        )
        for ln in rows[:limit]
    ]
    return Page(items=items, nextCursor=None)


@router.get("/me/sim-profile", response_model=SimProfileRead)
async def get_sim_profile(
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    line = (
        await session.execute(
            select(MobileLine).where(
                MobileLine.customer_id == customer.id, MobileLine.deleted_at.is_(None)
            )
        )
    ).scalars().first()
    if line is None or line.sim_id is None:
        raise not_found("No SIM profile for this customer")
    sim = (
        await session.execute(select(SIMProfile).where(SIMProfile.id == line.sim_id))
    ).scalar_one()
    return SimProfileRead(
        simId=sim.public_id,
        iccid=sim.iccid,
        imsiAlias=sim.imsi_alias,
        type=sim.sim_type,
        status=sim.status,
        activationDate=sim.activation_date,
    )


def _sim_to_read(sim: SIMProfile) -> SimProfileRead:
    return SimProfileRead(
        simId=sim.public_id,
        iccid=sim.iccid,
        imsiAlias=sim.imsi_alias,
        type=sim.sim_type,
        status=sim.status,
        activationDate=sim.activation_date,
    )


@router.post("/me/sim-swap", response_model=SimSwapResult)
async def sim_swap(
    body: SimSwapRequest,
    request: Request,
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    line = (
        await session.execute(
            select(MobileLine)
            .where(MobileLine.customer_id == customer.id, MobileLine.deleted_at.is_(None))
            .options(selectinload(MobileLine.sim))
        )
    ).scalars().first()
    if line is None:
        raise not_found("No mobile line for this customer")

    old_sim = line.sim
    if old_sim is not None:
        old_sim.status = "swapped"

    new_iccid = "89" + secrets.token_hex(10)[:20]
    new_sim = SIMProfile(
        public_id=await next_sim_id(session),
        iccid=new_iccid,
        imsi_alias=f"IMSI-{secrets.token_hex(6).upper()}",
        sim_type=body.newSimType,
        status="active",
        activation_date=date.today(),
    )
    session.add(new_sim)
    await session.flush()

    line.sim_id = new_sim.id
    await session.flush()

    await write_audit(
        session,
        event_type="SIM_SWAP_REQUEST",
        actor_id=customer.public_id,
        target_type="sim",
        target_id=new_sim.public_id,
        payload={
            "oldSimId": old_sim.public_id if old_sim else None,
            "newSimType": body.newSimType,
            "reason": body.reason,
        },
        ip_address=request.client.host if request.client else None,
    )

    return SimSwapResult(
        oldSim=_sim_to_read(old_sim) if old_sim else _sim_to_read(new_sim),
        newSim=_sim_to_read(new_sim),
    )
