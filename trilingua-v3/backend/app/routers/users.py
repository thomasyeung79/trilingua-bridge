"""User profile endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/me")
async def get_profile():
    """Get the current user's profile."""
    pass


@router.patch("/me")
async def update_profile():
    """Update the current user's profile."""
    pass


@router.delete("/me")
async def delete_account():
    """Delete the current user's account and data."""
    pass
