from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models import UserApiKey
from ..schemas import ApiKeyOut, ApiKeyUpsert, UserCreate, UserOut
from ..services.crypto import decrypt_secret, encrypt_secret, mask_secret
from ..services.orchestrator import get_or_create_user
from ..services.routing import ROUTING_TABLE

router = APIRouter(prefix="/api", tags=["auth-keys"])


@router.post("/users", response_model=UserOut)
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await get_or_create_user(db, body.email, body.display_name)
    return user


@router.get("/users/by-email", response_model=UserOut)
async def get_user(email: str = Query(...), db: AsyncSession = Depends(get_db)):
    user = await get_or_create_user(db, email)
    return user


@router.get("/users/{user_id}/keys", response_model=list[ApiKeyOut])
async def list_keys(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserApiKey).where(UserApiKey.user_id == user_id))
    keys = []
    for row in result.scalars().all():
        plain = decrypt_secret(row.encrypted_key)
        keys.append(
            ApiKeyOut(
                id=row.id,
                provider=row.provider,
                label=row.label,
                masked_key=mask_secret(plain),
                updated_at=row.updated_at,
            )
        )
    return keys


@router.put("/users/{user_id}/keys", response_model=ApiKeyOut)
async def upsert_key(user_id: int, body: ApiKeyUpsert, db: AsyncSession = Depends(get_db)):
    if body.provider.value == "mock":
        raise HTTPException(400, "Cannot store a mock provider key")
    result = await db.execute(
        select(UserApiKey).where(UserApiKey.user_id == user_id, UserApiKey.provider == body.provider)
    )
    row = result.scalar_one_or_none()
    if row:
        row.encrypted_key = encrypt_secret(body.api_key)
        row.label = body.label
    else:
        row = UserApiKey(
            user_id=user_id,
            provider=body.provider,
            encrypted_key=encrypt_secret(body.api_key),
            label=body.label,
        )
        db.add(row)
    await db.commit()
    await db.refresh(row)
    return ApiKeyOut(
        id=row.id,
        provider=row.provider,
        label=row.label,
        masked_key=mask_secret(body.api_key),
        updated_at=row.updated_at,
    )


@router.get("/routing")
async def get_routing():
    return {category.value: provider.value for category, provider in ROUTING_TABLE.items()}
