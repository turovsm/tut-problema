import uuid
from datetime import datetime

from app.domain.entities.enums import (
    IssueType,
    ReportStatus,
    UserRole,
    VoteType,
)
from app.domain.entities.location import Location
from app.domain.entities.report import (
    Report,
    ReportPhoto,
    ReportResolution,
    ResolutionPhoto,
)
from app.domain.entities.user import User
from app.domain.entities.vote import Vote
from app.presentation.api.schemas.reports import ReportResponse
from app.presentation.api.schemas.votes import VoteResponse
from app.presentation.api.v1.mappers import ReportMapper, VoteMapper


class TestMappers:
    def test_vote_mapper_to_response(self):
        vote_id = uuid.uuid4()
        user_id = uuid.uuid4()
        report_id = uuid.uuid4()

        vote_entity = Vote(
            id=vote_id,
            user_id=user_id,
            report_id=report_id,
            is_confirm=True,
            user_location=Location(longitude=10.0, latitude=20.0),
            is_verified=True,
            created_at=datetime.now(),
        )

        response = VoteMapper.to_vote_response(vote_entity)

        assert isinstance(response, VoteResponse)
        assert response.id == vote_id
        assert response.vote_type == VoteType.CONFIRM
        assert response.is_verified is True

    def test_report_mapper_to_response(self):
        report_id = uuid.uuid4()
        user_id = uuid.uuid4()
        photo_id = uuid.uuid4()
        assignee_id = uuid.uuid4()
        res_id = uuid.uuid4()

        creator = User(
            id=user_id,
            email="test@test.com",
            username="testuser",
            password_hash="hash",
            role=UserRole.USER,
        )

        assignee = User(
            id=assignee_id,
            email="test2@test.com",
            username="testuser2",
            password_hash="hash",
            role=UserRole.USER,
        )

        photo = ReportPhoto(
            id=photo_id,
            report_id=report_id,
            file_name="img.jpg",
            file_path="/tmp/img.jpg",
        )

        res_photo = ResolutionPhoto(
            id=uuid.uuid4(),
            resolution_id=res_id,
            file_name="done.jpg",
            file_path="path/done.jpg",
        )

        resolution = ReportResolution(
            id=res_id,
            report_id=report_id,
            resolved_by_id=assignee_id,
            comment="Resolved",
            photos=[res_photo],
        )

        report_entity = Report(
            id=report_id,
            title="Pothole on Main St",
            description="Very deep",
            issue_type=IssueType.POTHOLE,
            location=Location(longitude=30.0, latitude=50.0),
            user_location=Location(longitude=30.1, latitude=50.1),
            created_by_id=user_id,
            status=ReportStatus.PENDING,
            photos=[photo],
            created_by=creator,
            current_user_vote=VoteType.DISMISS,
            assigned_to_id=assignee_id,
            assigned_to=assignee,
            resolution=resolution,
        )

        response = ReportMapper.to_report_response(report_entity)

        assert isinstance(response, ReportResponse)
        assert response.id == report_id
        assert response.title == "Pothole on Main St"

        assert response.location.coordinates == [30.0, 50.0]

        assert response.created_by.id == user_id
        assert response.created_by.username == "testuser"

        assert response.assigned_to is not None
        assert response.assigned_to.id == assignee_id
        assert response.assigned_to.username == "testuser2"

        assert len(response.photos) == 1
        assert response.photos[0].id == photo_id
        assert response.photos[0].file_url == f"/api/uploads/photos/{photo_id}"

        assert response.resolution is not None
        assert response.resolution.id == res_id
        assert response.resolution.comment == "Resolved"
        assert len(response.resolution.photos) == 1
        assert (
            response.resolution.photos[0].file_url
            == f"/api/uploads/resolutions/{res_photo.id}"
        )

        assert response.user_vote == VoteType.DISMISS
