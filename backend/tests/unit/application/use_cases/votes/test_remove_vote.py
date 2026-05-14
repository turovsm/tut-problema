import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.use_cases.votes.remove_vote import RemoveVoteUseCase
from app.domain.entities.vote import Vote
from app.domain.exceptions.base import EntityNotFoundException


class TestRemoveVoteUseCase:
    @pytest.fixture
    def mock_vote_repo(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_vote_repo):
        return RemoveVoteUseCase(vote_repo=mock_vote_repo)

    async def test_remove_vote_success(self, use_case, mock_vote_repo):
        user_id = uuid.uuid4()
        report_id = uuid.uuid4()

        mock_vote_repo.get_user_vote.return_value = MagicMock(spec=Vote)

        await use_case.execute(user_id=user_id, report_id=report_id)

        mock_vote_repo.get_user_vote.assert_called_once_with(
            user_id=user_id, report_id=report_id
        )
        mock_vote_repo.delete.assert_called_once_with(
            user_id=user_id, report_id=report_id
        )

    async def test_remove_vote_not_found(self, use_case, mock_vote_repo):
        user_id = uuid.uuid4()
        report_id = uuid.uuid4()

        mock_vote_repo.get_user_vote.return_value = None

        with pytest.raises(EntityNotFoundException) as exc:
            await use_case.execute(user_id=user_id, report_id=report_id)

        assert "Vote not found" in exc.value.message
        mock_vote_repo.delete.assert_not_called()
