from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends, Query

from app.api.deps import get_current_active_user, get_current_verified_user, get_current_moderator, get_user_repo, \
    get_vote_repo
from app.core.config import settings
from app.database.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.vote_repository import VoteRepository
from app.schemas.common import SuccessResponse
from app.schemas.user import UserUpdate, UserResponse
from app.schemas.vote import VoteResponse

router = APIRouter()


@router.get("/me")
async def get_my_profile(current_user: Annotated[User, Depends(get_current_active_user)]):
    return SuccessResponse(data=UserResponse.model_validate(current_user).model_dump())


@router.put("/me")
async def update_my_profile(
        user_data: UserUpdate,
        current_user: Annotated[User, Depends(get_current_verified_user)],
        user_repo: Annotated[UserRepository, Depends(get_user_repo)]
):
    if user_data.username:
        existing = await user_repo.get_by_username(user_data.username)
        if existing and existing.id != current_user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

        current_user.username = user_data.username
        await user_repo.db.commit()
        await user_repo.db.refresh(current_user)

    return SuccessResponse(data=UserResponse.model_validate(current_user).model_dump())


@router.get("/me/votes")
async def get_my_votes(
        current_user: Annotated[User, Depends(get_current_active_user)],
        vote_repo: Annotated[VoteRepository, Depends(get_vote_repo)],
        page: int = Query(1, ge=1),
        limit: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE)
):
    offset = (page - 1) * limit
    votes, total = await vote_repo.get_user_votes_paginated(current_user.id, limit, offset)

    items = [VoteResponse.model_validate(v).model_dump() for v in votes]
    return SuccessResponse(data={"items": items, "total": total, "page": page, "limit": limit})


@router.get("/{user_id}")
async def get_user_profile(
        user_id: UUID,
        user_repo: Annotated[UserRepository, Depends(get_user_repo)],
        _: Annotated[User, Depends(get_current_active_user)]
):
    user = await user_repo.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return SuccessResponse(data=UserResponse.model_validate(user).model_dump())


@router.get("/admin/users")
async def list_all_users(
        user_repo: Annotated[UserRepository, Depends(get_user_repo)],
        _: Annotated[User, Depends(get_current_moderator)]
):
    users = await user_repo.get_all()
    items = [UserResponse.model_validate(u).model_dump() for u in users]
    return SuccessResponse(data={"items": items, "total": len(items)})
