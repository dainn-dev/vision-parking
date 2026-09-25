from fastapi import APIRouter

from app.api.v1 import auth, ops, platform, public, tenant

api_router = APIRouter()
api_router.include_router(public.router)
api_router.include_router(auth.router)
api_router.include_router(platform.router)
api_router.include_router(ops.router)
api_router.include_router(tenant.router)
