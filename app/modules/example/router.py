"""API 参考模块；项目扩展后可替换为实际的领域模块。"""

from fastapi import APIRouter

from app.schemas.example import PingResponse

router = APIRouter(prefix="/examples", tags=["examples"])


@router.get("/ping", response_model=PingResponse)
async def ping() -> PingResponse:
    return PingResponse(message="pong")
