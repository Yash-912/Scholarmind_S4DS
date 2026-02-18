"""
FastAPI Dependencies — Shared dependency injection for route handlers.
"""

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.database import get_db
from app.db import crud


async def get_current_user(
    x_user: Optional[str] = Header(None, alias="X-User"),
    db: AsyncSession = Depends(get_db),
):
    """
    Simple user identification via X-User header.
    Creates user if doesn't exist.
    """
    username = x_user or "anonymous"
    user = await crud.get_or_create_user(db, username)
    return user
