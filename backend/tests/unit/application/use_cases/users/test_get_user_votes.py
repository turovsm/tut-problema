import uuid
from unittest.mock import AsyncMock

import pytest

from app.application.dto.users import GetUserVotesDTO
from app.application.use_cases.users.get_user_votes import GetUserVotesUseCase
from app.domain.entities.location import Location
from app.domain.entities.vote import Vote


class TestGetUserVotesUseCase:
    @pytest.fixture
    def mock_vote_repo(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_vote_repo):
        return GetUserVotesUseCase(vote_repo=mock_vote_repo)

    @pytest.fixture
    def sample_votes(self):
        user_id = uuid.uuid4()
        return [
            Vote(
                id=uuid.uuid4(),
                user_id=user_id,
                report_id=uuid.uuid4(),
                is_confirm=True,
                user_location=Location(0, 0),
            ),
            Vote(
                id=uuid.uuid4(),
                user_id=user_id,
                report_id=uuid.uuid4(),
                is_confirm=False,
                user_location=Location(1, 1),
            ),
        ], 2

    async def test_get_user_votes_success(
        self, use_case, mock_vote_repo, sample_votes
    ):
        votes_list, total_count = sample_votes
        user_id = votes_list[0].user_id
        mock_vote_repo.get_user_votes_paginated.return_value = (
            votes_list,
            total_count,
        )

        dto = GetUserVotesDTO(user_id=user_id, page=3, limit=10)

        items, total = await use_case.execute(dto)

        mock_vote_repo.get_user_votes_paginated.assert_called_once_with(
            user_id=user_id, limit=10, offset=20
        )

        assert total == 2
        assert len(items) == 2
        assert items[0].is_confirm is True

    async def test_get_user_votes_empty(self, use_case, mock_vote_repo):
        user_id = uuid.uuid4()
        mock_vote_repo.get_user_votes_paginated.return_value = ([], 0)

        dto = GetUserVotesDTO(user_id=user_id)
        items, total = await use_case.execute(dto)

        assert total == 0
        assert items == []
