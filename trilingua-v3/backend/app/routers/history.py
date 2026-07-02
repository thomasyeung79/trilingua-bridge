"""History and workspace endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_history():
    """List the user's AI task history with filters."""
    pass


@router.delete("/{history_id}")
async def delete_history():
    """Delete a specific history entry."""
    pass
