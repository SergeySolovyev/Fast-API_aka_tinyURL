from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.cache import delete_cache, get_cache, set_cache
from src.database import get_async_session
from src.auth.users import current_active_user, current_user_optional
from src.auth.models import User
from src.links.models import Link
from src.links.schemas import LinkCreate, LinkResponse, LinkStats, LinkUpdate
from src.links.service import (
    create_short_link,
    get_link_by_short_code,
    search_link_by_url,
    build_short_url
)

router = APIRouter(
    prefix="/links",
    tags=["Links"]
)


@router.post("/shorten", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def shorten_url(
    link_data: LinkCreate,
    session: AsyncSession = Depends(get_async_session),
    user: Optional[User] = Depends(current_user_optional)
):
    """
    Create a shortened URL
    - Accessible for both authenticated and anonymous users
    - Can specify custom alias
    - Can set expiration time
    """
    try:
        user_id = user.id if user else None
        link = await create_short_link(
            session=session,
            original_url=str(link_data.original_url),
            user_id=user_id,
            custom_alias=link_data.custom_alias,
            expires_at=link_data.expires_at,
            category=link_data.category
        )
        await delete_cache(f"stats:{link.short_code}", f"redirect:{link.short_code}")
        
        return LinkResponse(
            id=link.id,
            short_code=link.short_code,
            original_url=link.original_url,
            short_url=build_short_url(link.short_code),
            custom_alias=link.custom_alias,
            created_at=link.created_at,
            expires_at=link.expires_at,
            click_count=link.click_count
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{short_code}/stats", response_model=LinkStats)
async def get_link_stats(
    short_code: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get statistics for a shortened link
    - Cached for 30 seconds
    """
    cached = await get_cache(f"stats:{short_code}")
    if cached:
        return LinkStats(**cached)

    link = await get_link_by_short_code(session, short_code)
    
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short link not found"
        )

    stats = LinkStats(
        short_code=link.short_code,
        original_url=link.original_url,
        created_at=link.created_at,
        expires_at=link.expires_at,
        click_count=link.click_count,
        last_used_at=link.last_used_at,
        category=link.category
    )

    await set_cache(f"stats:{short_code}", stats.model_dump(mode="json"), expire=30)
    return stats


@router.delete("/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    short_code: str,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """
    Delete a shortened link
    - Only accessible for authenticated users
    - Users can only delete their own links
    """
    link = await get_link_by_short_code(session, short_code)
    
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short link not found"
        )
    
    # Check ownership
    if link.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own links"
        )
    
    await delete_cache(f"stats:{link.short_code}", f"redirect:{link.short_code}")
    await session.delete(link)
    await session.commit()


@router.put("/{short_code}", response_model=LinkResponse)
async def update_link(
    short_code: str,
    link_update: LinkUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """
    Update a shortened link
    - Only accessible for authenticated users
    - Users can only update their own links
    """
    link = await get_link_by_short_code(session, short_code)
    
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short link not found"
        )
    
    # Check ownership
    if link.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own links"
        )
    
    # Update fields
    if link_update.original_url:
        link.original_url = str(link_update.original_url)
    if link_update.expires_at is not None:
        link.expires_at = link_update.expires_at
    if link_update.category is not None:
        link.category = link_update.category
    
    await session.commit()
    await session.refresh(link)
    await delete_cache(f"stats:{link.short_code}", f"redirect:{link.short_code}")
    
    return LinkResponse(
        id=link.id,
        short_code=link.short_code,
        original_url=link.original_url,
        short_url=build_short_url(link.short_code),
        custom_alias=link.custom_alias,
        created_at=link.created_at,
        expires_at=link.expires_at,
        click_count=link.click_count
    )


@router.get("/search/by-url", response_model=list[LinkResponse])
async def search_links(
    original_url: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Search for links by original URL
    """
    links = await search_link_by_url(session, original_url)
    
    return [
        LinkResponse(
            id=link.id,
            short_code=link.short_code,
            original_url=link.original_url,
            short_url=build_short_url(link.short_code),
            custom_alias=link.custom_alias,
            created_at=link.created_at,
            expires_at=link.expires_at,
            click_count=link.click_count
        )
        for link in links
    ]


@router.get("/user/my-links", response_model=list[LinkResponse])
async def get_my_links(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """
    Get all links created by the current user
    """
    result = await session.execute(
        select(Link).where(Link.user_id == user.id).order_by(Link.created_at.desc())
    )
    links = result.scalars().all()
    
    return [
        LinkResponse(
            id=link.id,
            short_code=link.short_code,
            original_url=link.original_url,
            short_url=build_short_url(link.short_code),
            custom_alias=link.custom_alias,
            created_at=link.created_at,
            expires_at=link.expires_at,
            click_count=link.click_count
        )
        for link in links
    ]
