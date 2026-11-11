"""第一版 API 路由组装。"""

from fastapi import APIRouter

from app.modules.example.router import router as example_router

router = APIRouter()
router.include_router(example_router)
