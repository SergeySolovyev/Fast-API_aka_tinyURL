import random
import string
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from src.config import SHORT_CODE_LENGTH, DEFAULT_LINK_EXPIRATION_DAYS, BASE_URL
from src.links.models import Link


def generate_short_code(length: int = SHORT_CODE_LENGTH) -> str:
    """Generate a random short code"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))


async def create_short_link(
    session: AsyncSession,
    original_url: str,
    user_id: Optional[uuid.UUID] = None,
    custom_alias: Optional[str] = None,
    expires_at: Optional[datetime] = None,
    category: Optional[str] = None
) -> Link:
    """Create a new short link"""
    
    # Use custom alias or generate short code
    if custom_alias:
        short_code = custom_alias
        # Check if custom alias already exists
        existing = await session.execute(
            select(Link).where(Link.custom_alias == custom_alias)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Custom alias '{custom_alias}' already exists")
    else:
        # Generate unique short code
        while True:
            short_code = generate_short_code()
            existing = await session.execute(
                select(Link).where(Link.short_code == short_code)
            )
            if not existing.scalar_one_or_none():
                break
    
    # Set default expiration if not provided
    if expires_at is None and DEFAULT_LINK_EXPIRATION_DAYS > 0:
        expires_at = datetime.utcnow() + timedelta(days=DEFAULT_LINK_EXPIRATION_DAYS)
    
    link = Link(
        short_code=short_code,
        original_url=str(original_url),
        custom_alias=custom_alias,
        user_id=user_id,
        expires_at=expires_at,
        category=category
    )
    
    session.add(link)
    await session.commit()
    await session.refresh(link)
    
    return link


async def get_link_by_short_code(session: AsyncSession, short_code: str) -> Optional[Link]:
    """Get link by short code"""
    result = await session.execute(
        select(Link).where(Link.short_code == short_code)
    )
    return result.scalar_one_or_none()


async def increment_click_count(session: AsyncSession, link_id: uuid.UUID):
    """Increment click count and update last_used_at"""
    await session.execute(
        update(Link)
        .where(Link.id == link_id)
        .values(
            click_count=Link.click_count + 1,
            last_used_at=datetime.utcnow()
        )
    )
    await session.commit()


async def search_link_by_url(session: AsyncSession, original_url: str) -> list[Link]:
    """Search links by original URL"""
    result = await session.execute(
        select(Link).where(Link.original_url == original_url)
    )
    return result.scalars().all()


async def delete_expired_links(session: AsyncSession) -> int:
    """Delete all expired links and return count"""
    now = datetime.utcnow()
    result = await session.execute(
        select(Link).where(Link.expires_at <= now)
    )
    expired_links = result.scalars().all()
    
    for link in expired_links:
        await session.delete(link)
    
    await session.commit()
    return len(expired_links)


async def delete_unused_links(session: AsyncSession, days: int) -> int:
    """Delete links not used for `days` days and return count"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    # A link is "unused" if last_used_at < cutoff  OR  (never used AND created_at < cutoff)
    result = await session.execute(
        select(Link).where(
            (Link.last_used_at < cutoff)
            | ((Link.last_used_at.is_(None)) & (Link.created_at < cutoff))
        )
    )
    unused_links = result.scalars().all()
    for link in unused_links:
        await session.delete(link)
    await session.commit()
    return len(unused_links)


def build_short_url(short_code: str) -> str:
    """Build full short URL from code"""
    return f"{BASE_URL}/{short_code}"
