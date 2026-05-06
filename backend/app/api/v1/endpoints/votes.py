from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends
from app.api.deps import get_current_verified_user, get_current_active_user, get_vote_service
from app.database.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.vote import VoteCreate, VoteResponse, VoteStatsResponse
from app.services.vote_service import VoteService

router = APIRouter()

@router.post("/reports/{report_id}", status_code=status.HTTP_201_CREATED, response_model=SuccessResponse[VoteResponse])
async def vote_for_report(report_id: UUID, vote_data: VoteCreate, current_user: Annotated[User, Depends(get_current_verified_user)], vote_service: Annotated[VoteService, Depends(get_vote_service)]):
    try:
        vote = await vote_service.cast_vote(current_user.id, report_id, vote_data)
        return SuccessResponse(data=vote, message="Vote created successfully")
    except ValueError as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.get("/reports/{report_id}/my-vote", response_model=SuccessResponse[VoteResponse])
async def get_my_vote(report_id: UUID, current_user: Annotated[User, Depends(get_current_verified_user)], vote_service: Annotated[VoteService, Depends(get_vote_service)]):
    vote = await vote_service.vote_repo.get_user_vote(current_user.id, report_id)
    return SuccessResponse(data=vote) if vote else SuccessResponse(data=None)

@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_vote(report_id: UUID, current_user: Annotated[User, Depends(get_current_verified_user)], vote_service: Annotated[VoteService, Depends(get_vote_service)]):
    try:
        await vote_service.remove_vote(current_user.id, report_id)
        return None
    except ValueError as e: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/reports/{report_id}/stats", response_model=SuccessResponse[VoteStatsResponse])
async def get_report_vote_stats(report_id: UUID, vote_service: Annotated[VoteService, Depends(get_vote_service)], _: Annotated[User, Depends(get_current_active_user)]):
    stats = await vote_service.vote_repo.get_report_vote_stats(report_id)
    return SuccessResponse(data={"report_id": str(report_id), **stats})