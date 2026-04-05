from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import Vote, Report
from app.database import get_db
from app.dependencies import get_current_active_user, get_current_verified_user
from app.logging_config import get_logger
from app.schemas import VoteCreate, Vote as VoteSchema, SuccessResponse
from app.utils.distance import calculate_distance_haversine

router = APIRouter(prefix="/votes", tags=["Votes"])
logger = get_logger("app.routers.votes")


@router.post("/reports/{report_id}", status_code=status.HTTP_201_CREATED)
async def vote_for_report(
        report_id: UUID,
        vote_data: VoteCreate,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_verified_user)
):
    logger.info(
        "Vote attempted",
        user_id=str(current_user.id),
        report_id=str(report_id),
        vote_type=vote_data.vote_type
    )
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    if report.created_by_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot vote on your own report"
        )

    user_lng, user_lat = vote_data.user_location.coordinates

    report_point_text = await db.scalar(select(report.location.ST_AsText()))
    report_coords = report_point_text.replace("POINT(", "").replace(")", "").split()
    report_lat = float(report_coords[1])
    report_lon = float(report_coords[0])

    distance = calculate_distance_haversine(
        user_lat, user_lng,
        report_lat, report_lon
    )

    if distance > settings.MAX_VOTE_DISTANCE_METERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot vote on report {distance:.0f} meters away. "
                   f"You must be within {settings.MAX_VOTE_DISTANCE_METERS} meters to vote."
        )

    result = await db.execute(
        select(Vote).where(
            Vote.user_id == current_user.id,
            Vote.report_id == report_id
        )
    )
    existing = result.scalar_one_or_none()

    is_confirm = vote_data.vote_type == "confirm"
    user_point = Point(user_lng, user_lat)

    is_verified = False
    if vote_data.accuracy:
        if distance <= (vote_data.accuracy + settings.VOTE_VERIFICATION_BUFFER_METERS):
            is_verified = True

    if existing:
        existing.is_confirm = is_confirm
        existing.user_location = from_shape(user_point, srid=4326)
        existing.is_verified = is_verified
        await db.commit()
        return SuccessResponse(message="Vote updated successfully")

    vote = Vote(
        user_id=current_user.id,
        report_id=report_id,
        is_confirm=is_confirm,
        user_location=from_shape(user_point, srid=4326),
        is_verified=is_verified
    )
    db.add(vote)
    await db.commit()
    await db.refresh(vote)

    logger.info("Vote recorded successfully", vote_id=str(vote.id))

    return SuccessResponse(
        data=VoteSchema(
            id=vote.id,
            report_id=vote.report_id,
            vote_type=vote_data.vote_type,
            is_verified=is_verified,
            created_at=vote.created_at
        ).model_dump(),
        message="Vote created successfully"
    )


@router.get("/reports/{report_id}/my-vote")
async def get_my_vote(
        report_id: UUID,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_verified_user)
):
    result = await db.execute(
        select(Vote).where(
            Vote.user_id == current_user.id,
            Vote.report_id == report_id
        )
    )
    vote = result.scalar_one_or_none()

    if not vote:
        return SuccessResponse(data=None)

    return SuccessResponse(
        data=VoteSchema(
            id=vote.id,
            report_id=vote.report_id,
            vote_type="confirm" if vote.is_confirm else "dismiss",
            is_verified=vote.is_verified,
            created_at=vote.created_at
        ).model_dump()
    )


@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_vote(
        report_id: UUID,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_verified_user)
):
    result = await db.execute(
        select(Vote).where(
            Vote.user_id == current_user.id,
            Vote.report_id == report_id
        )
    )
    vote = result.scalar_one_or_none()

    if not vote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vote not found")

    await db.delete(vote)
    await db.commit()
    return None


@router.get("/reports/{report_id}/stats")
async def get_report_vote_stats(
        report_id: UUID,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_active_user)
):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    confirm_result = await db.execute(
        select(func.count()).where(
            Vote.report_id == report_id,
            Vote.is_confirm.is_(True)
        )
    )
    confirm_count = confirm_result.scalar()

    dismiss_result = await db.execute(
        select(func.count()).where(
            Vote.report_id == report_id,
            Vote.is_confirm.is_(False)
        )
    )
    dismiss_count = dismiss_result.scalar()

    return SuccessResponse(
        data={
            "report_id": str(report_id),
            "confirm_count": confirm_count,
            "dismiss_count": dismiss_count,
            "total_votes": confirm_count + dismiss_count,
            "current_status": report.status
        }
    )
