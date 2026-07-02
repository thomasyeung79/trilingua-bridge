"""Usage quota and subscription endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def get_quota():
    """Get the current user's usage and remaining quota."""
    pass
