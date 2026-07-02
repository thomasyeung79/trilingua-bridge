"""Vocabulary and review book endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_vocab():
    """List the user's vocabulary items."""
    pass


@router.post("")
async def add_vocab():
    """Add a new vocabulary item."""
    pass


@router.delete("/{vocab_id}")
async def delete_vocab():
    """Delete a vocabulary item."""
    pass
