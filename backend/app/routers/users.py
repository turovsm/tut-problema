from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db, User, Vote
from app.dependencies import get_current_active_user, get_current_verified_user, get_current_moderator
from app.logging_config import get_logger
from app.schemas import UserUpdate, SuccessResponse, User as UserSchema, Vote as VoteSchema

router = APIRouter(prefix="/users", tags=["Users"])
logger = get_logger("app.routers.users")


@router.get("/me")
async def get_my_profile(current_user=Depends(get_current_active_user)):
    return SuccessResponse(data=UserSchema.model_validate(current_user).model_dump())


@router.put("/me")
async def update_my_profile(
        user_data: UserUpdate,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_verified_user)
):
    if user_data.username:
        logger.info("Username update attempted", user_id=str(current_user.id), new_username=user_data.username)
        result = await db.execute(select(User).where(User.username == user_data.username))
        existing = result.scalar_one_or_none()
        if existing and existing.id != current_user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

        current_user.username = user_data.username
        await db.commit()
        await db.refresh(current_user)
        logger.info("Username updated successfully", user_id=str(current_user.id))

    return SuccessResponse(data=UserSchema.model_validate(current_user).model_dump())


@router.get("/me/votes")
async def get_my_votes(
        page: int = Query(1, ge=1),
        limit: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_active_user)
):
    query = select(Vote).where(Vote.user_id == current_user.id)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    query = query.order_by(Vote.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    votes = result.scalars().all()

    items = []
    for vote in votes:
        items.append(VoteSchema(
            id=vote.id,
            report_id=vote.report_id,
            vote_type="confirm" if vote.is_confirm else "dismiss",
            is_verified=vote.is_verified,
            created_at=vote.created_at
        ))

    return SuccessResponse(data={
        "items": [item.model_dump() for item in items],
        "total": total,
        "page": page,
        "limit": limit
    })


@router.get("/{user_id}")
async def get_user_profile(
        user_id: UUID,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_active_user)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return SuccessResponse(data={
        "id": str(user.id),
        "username": user.username,
        "role": user.role,
        "created_at": user.created_at.isoformat()
    })


@router.get("/admin/users")
async def list_all_users(
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_moderator)
):
    result = await db.execute(select(User))
    users = result.scalars().all()

    return SuccessResponse(data={
        "items": [
            {
                "id": str(u.id),
                "email": u.email,
                "username": u.username,
                "role": u.role,
                "is_active": u.is_active,
                "is_verified": u.is_verified,
                "created_at": u.created_at.isoformat()
            }
            for u in users
        ],
        "total": len(users)
    })
