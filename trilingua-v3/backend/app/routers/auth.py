"""Authentication endpoints — register, login, refresh, logout."""
from fastapi import APIRouter

router = APIRouter()


@router.post("/register")
async def register():
    """Create a new user account."""
    pass


@router.post("/login")
async def login():
    """Authenticate and return JWT tokens."""
    pass


@router.post("/refresh")
async def refresh():
    """Refresh an expired access token."""
    pass


@router.post("/logout")
async def logout():
    """Invalidate the current refresh token."""
    pass
