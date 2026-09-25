"""Public endpoints: subscription plans, legal documents, tenant self-registration."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import errors, security
from app.core.audit import write_audit
from app.core.database import get_db
from app.core.deps import auth_db
from app.core.security import client_ip
from app.models import LegalDocument, SubscriptionPlan, Tenant, TenantUser
from app.schemas.auth import MessageResponse
from app.schemas.platform import LegalDocOut, PlanOut, TenantRegistration

router = APIRouter(tags=["public"])


@router.get("/plans", response_model=list[PlanOut])
async def list_plans(db: AsyncSession = Depends(get_db)) -> list[SubscriptionPlan]:
    rows = (await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.is_public))).scalars()
    return list(rows)


@router.get("/legal/{doc_type}", response_model=list[LegalDocOut])
async def list_legal_docs(doc_type: str, db: AsyncSession = Depends(get_db)) -> list[LegalDocument]:
    rows = (
        await db.execute(
            select(LegalDocument)
            .where(LegalDocument.doc_type == doc_type.upper(), LegalDocument.is_active)
            .order_by(LegalDocument.published_at.desc())
        )
    ).scalars()
    return list(rows)


@router.post("/register", response_model=MessageResponse, status_code=201)
async def register_tenant(
    body: TenantRegistration, request: Request, db: AsyncSession = Depends(auth_db)
) -> MessageResponse:
    """Self-service tenant signup → TRIAL tenant + invited TENANT_ADMIN."""

    exists = (
        await db.execute(
            select(func.count()).select_from(Tenant).where(Tenant.code == body.organization_code.upper())
        )
    ).scalar_one()
    if exists:
        raise errors.conflict("TENANT_CODE_EXISTS", "Organization code already registered")

    email_taken = (
        await db.execute(
            select(func.count())
            .select_from(TenantUser)
            .where(TenantUser.email == body.administrator.email.lower())
        )
    ).scalar_one()
    if email_taken:
        raise errors.conflict("EMAIL_EXISTS", "Administrator email already registered")

    tenant = Tenant(
        name=body.organization_name,
        code=body.organization_code.upper(),
        email=body.email.lower(),
        phone=body.phone,
        timezone=body.timezone,
        status="TRIAL",
    )
    db.add(tenant)
    await db.flush()

    admin = TenantUser(
        tenant_id=tenant.id,
        name=body.administrator.name,
        email=body.administrator.email.lower(),
        phone=body.administrator.phone,
        role="TENANT_ADMIN",
        status="INVITED",
        password_hash=security.hash_password(body.administrator.password)
        if body.administrator.password
        else None,
    )
    db.add(admin)
    await write_audit(
        db,
        category="TENANT_MANAGEMENT",
        action="TENANT_SELF_REGISTERED",
        actor_type="SYSTEM",
        tenant_id=tenant.id,
        tenant_name=tenant.name,
        resource_type="TENANT",
        resource_id=str(tenant.id),
        resource_name=tenant.name,
        source="API",
        ip_address=client_ip(request),
        metadata={"planCode": body.plan_code},
    )
    await db.commit()

    return MessageResponse(
        message="Registration accepted. The tenant is provisioned in TRIAL status; "
        "the administrator will receive an invitation email to activate the account."
    )
