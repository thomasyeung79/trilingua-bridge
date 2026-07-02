"""Chat Coach endpoints — reply suggestions, tone analysis, conversation memory."""
from fastapi import APIRouter

router = APIRouter()


@router.post("")
async def coach():
    """Generate reply suggestions with tone analysis and cultural notes."""
    pass


@router.post("/stream")
async def coach_stream():
    """Streaming coach response via SSE."""
    pass
