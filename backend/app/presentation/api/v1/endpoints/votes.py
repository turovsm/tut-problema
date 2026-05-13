from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.application.dto.votes import CastVoteDTO
from app.domain.entities.user import User
from app.presentation.api.deps import (
    get_cast_vote_use_case,
    get_current_user,
    get_current_verified_user,
    get_my_vote_use_case,
    get_remove_vote_use_case,
    get_vote_stats_use_case,
)
from app.presentation.api.schemas.common import SuccessResponse
from app.presentation.api.schemas.votes import (
    VoteCreate,
    VoteResponse,
    VoteStatsResponse,
)
from app.presentation.api.v1.mappers import VoteMapper

router = APIRouter()


@router.post(
    "/reports/{report_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[VoteResponse],
)
async def vote_for_report(
    report_id: UUID,
    data: VoteCreate,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    use_case: Annotated[Depends, Depends(get_cast_vote_use_case)],
):
    vote = await use_case.execute(
        CastVoteDTO(
            user_id=current_user.id,
            report_id=report_id,
            vote_type=data.vote_type,
            user_location_lat=data.user_location_lat,
            user_location_lng=data.user_location_lng,
            accuracy=data.accuracy,
        )
    )
    return SuccessResponse(
        data=VoteMapper.to_vote_response(vote),
        message="Vote recorded successfully",
    )


@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_vote(
    report_id: UUID,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    use_case: Annotated[Depends, Depends(get_remove_vote_use_case)],
):
    await use_case.execute(user_id=current_user.id, report_id=report_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/reports/{report_id}/my-vote",
    response_model=SuccessResponse[VoteResponse],
)
async def get_my_vote(
    report_id: UUID,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    use_case: Annotated[Depends, Depends(get_my_vote_use_case)],
):
    vote = await use_case.execute(user_id=current_user.id, report_id=report_id)
    return SuccessResponse(
        data=VoteMapper.to_vote_response(vote) if vote else None
    )


@router.get(
    "/reports/{report_id}/stats",
    response_model=SuccessResponse[VoteStatsResponse],
)
async def get_report_vote_stats(
    report_id: UUID,
    use_case: Annotated[Depends, Depends(get_vote_stats_use_case)],
    _: Annotated[User, Depends(get_current_user)],
):
    stats_dto = await use_case.execute(report_id)
    return SuccessResponse(
        data=VoteStatsResponse(
            report_id=stats_dto.report_id,
            confirm_count=stats_dto.confirm_count,
            dismiss_count=stats_dto.dismiss_count,
            current_status=stats_dto.current_status,
        )
    )
