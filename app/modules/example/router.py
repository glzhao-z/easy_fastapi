"""Reference API module; replace it with real domain modules as the project grows."""

from fastapi import APIRouter

from app.schemas.example import PingResponse

router = APIRouter(prefix="/examples", tags=["examples"])


@router.get("/ping", response_model=PingResponse)
async def ping() -> PingResponse:
    return PingResponse(message="pong")
