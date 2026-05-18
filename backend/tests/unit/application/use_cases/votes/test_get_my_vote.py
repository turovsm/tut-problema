import uuid
from unittest.mock import AsyncMock

import pytest

from app.application.use_cases.votes.get_my_vote import GetMyVoteUseCase
from app.domain.entities.location import Location
from app.domain.entities.vote import Vote


class TestGetMyVoteUseCase:
    @pytest.fixture
    def mock_vote_repo(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_vote_repo):
        return GetMyVoteUseCase(vote_repo=mock_vote_repo)

    async def test_get_my_vote_exists(self, use_case, mock_vote_repo):
        user_id = uuid.uuid4()
        report_id = uuid.uuid4()
        expected_vote = Vote(
            user_id=user_id,
            report_id=report_id,
            is_confirm=True,
            user_location=Location(longitude=0, latitude=0),
            is_verified=True,
        )

        mock_vote_repo.get_user_vote.return_value = expected_vote

        result = await use_case.execute(user_id=user_id, report_id=report_id)

        assert result == expected_vote
        assert result.is_confirm is True
        mock_vote_repo.get_user_vote.assert_called_once_with(
            user_id=user_id, report_id=report_id
        )

    async def test_get_my_vote_none(self, use_case, mock_vote_repo):
        user_id = uuid.uuid4()
        report_id = uuid.uuid4()

        mock_vote_repo.get_user_vote.return_value = None

        result = await use_case.execute(user_id=user_id, report_id=report_id)

        assert result is None
        mock_vote_repo.get_user_vote.assert_called_once()
