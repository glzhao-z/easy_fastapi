"""顶层路由组装。"""

from fastapi import APIRouter

from app.api.routes.system import router as system_routes
from app.api.v1.router import router as v1_routes

system_router = APIRouter()
system_router.include_router(system_routes)

api_v1_router = APIRouter()
api_v1_router.include_router(v1_routes)
