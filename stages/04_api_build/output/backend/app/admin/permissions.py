"""RBAC matrix — single source of truth derived from
`stages/08_phase2_requirements/output/admin-rbac-matrix.md`.

Stage 11 routers use `require_module(<module>, Access.RW)` to enforce access.
"""

from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    SUPPORT_AGENT = "support_agent"
    BILLING_OPERATOR = "billing_operator"
    PRODUCT_MANAGER = "product_manager"
    OPS_ADMIN = "ops_admin"
    SECURITY_ANALYST = "security_analyst"
    SUPPLIER_ADMIN = "supplier_admin"


class Module(str, Enum):
    CUSTOMER_SEARCH = "customer_search"
    CUSTOMER_BALANCE = "customer_balance"
    PLAN_CATALOG = "plan_catalog"
    PROMOTION_CATALOG = "promotion_catalog"
    COUPON_CATALOG = "coupon_catalog"
    TICKET_MANAGEMENT = "ticket_management"
    REFUND_WORKFLOW = "refund_workflow"
    AUDIT_LOG = "audit_log"
    REPORTING = "reporting"
    ADMIN_USERS_MANAGEMENT = "admin_users_management"


class Access(str, Enum):
    NONE = "-"
    READ = "R"
    READ_WRITE = "RW"


_R, _RW, _N = Access.READ, Access.READ_WRITE, Access.NONE

PERMISSIONS: dict[Role, dict[Module, Access]] = {
    Role.SUPPORT_AGENT: {
        Module.CUSTOMER_SEARCH: _R,
        Module.CUSTOMER_BALANCE: _N,
        Module.PLAN_CATALOG: _R,
        Module.PROMOTION_CATALOG: _R,
        Module.COUPON_CATALOG: _R,
        Module.TICKET_MANAGEMENT: _RW,
        Module.REFUND_WORKFLOW: _N,
        Module.AUDIT_LOG: _N,
        Module.REPORTING: _N,
        Module.ADMIN_USERS_MANAGEMENT: _N,
    },
    Role.BILLING_OPERATOR: {
        Module.CUSTOMER_SEARCH: _R,
        Module.CUSTOMER_BALANCE: _RW,
        Module.PLAN_CATALOG: _R,
        Module.PROMOTION_CATALOG: _R,
        Module.COUPON_CATALOG: _R,
        Module.TICKET_MANAGEMENT: _R,
        Module.REFUND_WORKFLOW: _RW,
        Module.AUDIT_LOG: _R,
        Module.REPORTING: _R,
        Module.ADMIN_USERS_MANAGEMENT: _N,
    },
    Role.PRODUCT_MANAGER: {
        Module.CUSTOMER_SEARCH: _R,
        Module.CUSTOMER_BALANCE: _N,
        Module.PLAN_CATALOG: _RW,
        Module.PROMOTION_CATALOG: _RW,
        Module.COUPON_CATALOG: _RW,
        Module.TICKET_MANAGEMENT: _R,
        Module.REFUND_WORKFLOW: _N,
        Module.AUDIT_LOG: _N,
        Module.REPORTING: _R,
        Module.ADMIN_USERS_MANAGEMENT: _N,
    },
    Role.OPS_ADMIN: {
        Module.CUSTOMER_SEARCH: _R,
        Module.CUSTOMER_BALANCE: _RW,
        Module.PLAN_CATALOG: _RW,
        Module.PROMOTION_CATALOG: _RW,
        Module.COUPON_CATALOG: _RW,
        Module.TICKET_MANAGEMENT: _RW,
        Module.REFUND_WORKFLOW: _RW,
        Module.AUDIT_LOG: _R,
        Module.REPORTING: _R,
        Module.ADMIN_USERS_MANAGEMENT: _RW,
    },
    Role.SECURITY_ANALYST: {
        Module.CUSTOMER_SEARCH: _R,
        Module.CUSTOMER_BALANCE: _N,
        Module.PLAN_CATALOG: _R,
        Module.PROMOTION_CATALOG: _R,
        Module.COUPON_CATALOG: _R,
        Module.TICKET_MANAGEMENT: _R,
        Module.REFUND_WORKFLOW: _N,
        Module.AUDIT_LOG: _R,
        Module.REPORTING: _R,
        Module.ADMIN_USERS_MANAGEMENT: _N,
    },
    Role.SUPPLIER_ADMIN: {m: _N for m in Module},  # zero-permission placeholder
}


def has_access(role: Role | str, module: Module | str, required: Access) -> bool:
    """Return True if `role` has at least `required` access on `module`."""
    r = Role(role) if not isinstance(role, Role) else role
    m = Module(module) if not isinstance(module, Module) else module
    granted = PERMISSIONS[r].get(m, Access.NONE)
    if required == Access.READ:
        return granted in (Access.READ, Access.READ_WRITE)
    if required == Access.READ_WRITE:
        return granted == Access.READ_WRITE
    return False  # NONE never grants
