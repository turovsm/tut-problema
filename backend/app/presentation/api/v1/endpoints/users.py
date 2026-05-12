from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.application.dto.users import (
    GetUserVotesDTO,
    ListUsersDTO,
    UpdateUserDTO,
)
from app.domain.entities.user import User
from app.presentation.api.deps import (
    get_current_moderator,
    get_current_user,
    get_current_verified_user,
    get_list_all_users_use_case,
    get_update_user_use_case,
    get_user_profile_use_case,
    get_user_votes_use_case,
)
from app.presentation.api.schemas.auth import (
    UserListQuery,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.presentation.api.schemas.common import SuccessResponse
from app.presentation.api.schemas.votes import (
    VoteListResponse,
    VoteQuery,
)
from app.presentation.api.v1.mappers import VoteMapper

router = APIRouter()


@router.get("/me", response_model=SuccessResponse[UserResponse])
async def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return SuccessResponse(data=UserResponse.model_validate(current_user))


@router.put("/me", response_model=SuccessResponse[UserResponse])
async def update_my_profile(
    data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    use_case: Annotated[Depends, Depends(get_update_user_use_case)],
):
    user = await use_case.execute(
        UpdateUserDTO(user_id=current_user.id, username=data.username)
    )
    return SuccessResponse(
        data=UserResponse.model_validate(user),
        message="Profile updated successfully",
    )


@router.get("/me/votes", response_model=SuccessResponse[VoteListResponse])
async def get_my_votes(
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[Depends, Depends(get_user_votes_use_case)],
    data: VoteQuery = Depends(),
):
    votes, total = await use_case.execute(
        GetUserVotesDTO(
            user_id=current_user.id, page=data.page, limit=data.limit
        )
    )

    return SuccessResponse(
        data=VoteListResponse(
            items=[VoteMapper.to_vote_response(v) for v in votes],
            total=total,
            page=data.page,
            limit=data.limit,
            has_next=data.page * data.limit < total,
        )
    )


@router.get("/{user_id}", response_model=SuccessResponse[UserResponse])
async def get_user_profile(
    user_id: UUID,
    use_case: Annotated[Depends, Depends(get_user_profile_use_case)],
    _: Annotated[User, Depends(get_current_user)],
):
    user = await use_case.execute(user_id)
    return SuccessResponse(data=UserResponse.model_validate(user))


@router.get("/admin/users", response_model=SuccessResponse[UserListResponse])
async def list_all_users(
    current_user: Annotated[User, Depends(get_current_moderator)],
    use_case: Annotated[Depends, Depends(get_list_all_users_use_case)],
    data: UserListQuery = Depends(),
):
    users, total = await use_case.execute(
        ListUsersDTO(
            user_role=current_user.role, page=data.page, limit=data.limit
        )
    )
    return SuccessResponse(
        data=UserListResponse(
            items=[UserResponse.model_validate(u) for u in users],
            total=total,
            page=data.page,
            limit=data.limit,
            has_next=data.page * data.limit < total,
        )
    )
