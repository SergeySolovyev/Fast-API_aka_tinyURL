from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_async_session
from src.links.service import get_link_by_short_code, increment_click_count

router = APIRouter(tags=["Redirect"])


@router.get("/{short_code}")
async def redirect_to_url(
    short_code: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Redirect to the original URL
    - Cached for 60 seconds for popular links
    - Increments click counter
    - Checks expiration
    """
    link = await get_link_by_short_code(session, short_code)
    
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short link not found"
        )
    
    # Check if link has expired
    if link.expires_at and link.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Short link has expired"
        )
    
    # Increment click count (in background)
    await increment_click_count(session, link.id)
    
    return RedirectResponse(url=link.original_url, status_code=307)
