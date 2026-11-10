"""Version 1 router composition."""

from fastapi import APIRouter

from app.modules.example.router import router as example_router

router = APIRouter()
router.include_router(example_router)
