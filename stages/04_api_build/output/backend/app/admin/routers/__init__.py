"""Admin portal routers. Each module is wired into the main FastAPI app in app/main.py."""

from fastapi import APIRouter

from . import (
    admin_users,
    audit,
    auth,
    customers,
    dashboard,
    plans,
    promotions,
    refunds,
    reports,
    tickets,
)

# Aggregate under `/admin` — paths are declared per-router with full prefix already.
admin_router = APIRouter(prefix="", tags=["admin"])
for module in (
    auth.router,
    dashboard.router,
    customers.router,
    plans.router,
    promotions.router,
    tickets.router,
    refunds.router,
    audit.router,
    reports.router,
    admin_users.router,
):
    admin_router.include_router(module)

__all__ = ["admin_router"]
