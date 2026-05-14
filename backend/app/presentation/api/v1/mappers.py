from app.domain.entities.enums import VoteType
from app.domain.entities.report import (
    Report,
    ReportPhoto,
    ReportResolution,
    ResolutionPhoto,
)
from app.domain.entities.vote import Vote
from app.presentation.api.schemas.auth import UserResponse
from app.presentation.api.schemas.common import Location
from app.presentation.api.schemas.reports import (
    ReportPhotoResponse,
    ReportResponse,
    ResolutionPhotoResponse,
    ResolutionResponse,
)
from app.presentation.api.schemas.votes import VoteResponse


class VoteMapper:
    @staticmethod
    def to_vote_response(vote: Vote) -> VoteResponse:
        return VoteResponse(
            id=vote.id,
            report_id=vote.report_id,
            vote_type=VoteType.CONFIRM
            if vote.is_confirm
            else VoteType.DISMISS,
            is_verified=vote.is_verified,
            created_at=vote.created_at,
        )


class ReportMapper:
    @staticmethod
    def to_photo_response(photo: ReportPhoto) -> ReportPhotoResponse:
        return ReportPhotoResponse(
            id=photo.id,
            file_name=photo.file_name,
            file_url=f"/api/uploads/photos/{photo.id}",
            uploaded_at=photo.uploaded_at,
        )

    @staticmethod
    def to_resolution_photo_response(
        photo: ResolutionPhoto,
    ) -> ResolutionPhotoResponse:
        return ResolutionPhotoResponse(
            id=photo.id,
            file_url=f"/api/uploads/resolutions/{photo.id}",
            uploaded_at=photo.uploaded_at,
        )

    @classmethod
    def to_resolution_response(
        cls, resolution: ReportResolution
    ) -> ResolutionResponse:
        return ResolutionResponse(
            id=resolution.id,
            comment=resolution.comment,
            resolved_at=resolution.resolved_at,
            photos=[
                cls.to_resolution_photo_response(p) for p in resolution.photos
            ],
        )

    @classmethod
    def to_report_response(cls, report: Report) -> ReportResponse:
        creator_data = None
        if hasattr(report, "created_by") and report.created_by:
            creator_data = UserResponse.model_validate(report.created_by)

        assignee_data = None
        if getattr(report, "assigned_to", None):
            assignee_data = UserResponse.model_validate(report.assigned_to)

        resolution_data = None
        if getattr(report, "resolution", None) and report.resolution:
            resolution_data = cls.to_resolution_response(report.resolution)

        return ReportResponse(
            id=report.id,
            title=report.title,
            description=report.description,
            issue_type=report.issue_type,
            location=Location(
                coordinates=[
                    report.location.longitude,
                    report.location.latitude,
                ]
            ),
            status=report.status,
            created_by=creator_data,
            assigned_to=assignee_data,
            resolution=resolution_data,
            created_at=report.created_at,
            updated_at=report.updated_at,
            photos=[cls.to_photo_response(p) for p in report.photos],
            user_vote=getattr(report, "current_user_vote", None),
        )
