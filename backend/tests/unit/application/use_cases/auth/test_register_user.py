import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dto.auth import RegisterUserDTO
from app.application.use_cases.auth.register_user import RegisterUserUseCase
from app.domain.entities.user import User
from app.domain.exceptions.user import (
    EmailAlreadyRegisteredException,
    UsernameTakenException,
)


class TestRegisterUserUseCase:
    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_token_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_auth_provider(self):
        provider = MagicMock()
        provider.hash_password.return_value = "hashed_password"
        return provider

    @pytest.fixture
    def mock_email_provider(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(
        self,
        mock_user_repo,
        mock_token_repo,
        mock_auth_provider,
        mock_email_provider,
    ):
        return RegisterUserUseCase(
            user_repo=mock_user_repo,
            token_repo=mock_token_repo,
            auth_provider=mock_auth_provider,
            email_provider=mock_email_provider,
            verification_token_expiry_hours=24,
        )

    async def test_register_success(
        self, use_case, mock_user_repo, mock_token_repo, mock_email_provider
    ):
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.get_by_username.return_value = None

        async def side_effect_save(user):
            user.id = uuid.uuid4()
            return user

        mock_user_repo.save.side_effect = side_effect_save

        dto = RegisterUserDTO(
            email="new@example.com",
            username="new_user",
            password="SecretPassword123!",
        )

        result = await use_case.execute(dto)

        assert isinstance(result, User)
        assert result.email == "new@example.com"
        assert result.password_hash == "hashed_password"

        mock_user_repo.save.assert_called_once()
        mock_token_repo.save_verification_token.assert_called_once()
        mock_email_provider.send_verification.assert_called_once()

    async def test_register_duplicate_email(self, use_case, mock_user_repo):
        mock_user_repo.get_by_email.return_value = MagicMock(spec=User)

        dto = RegisterUserDTO(
            email="exists@test.com", username="any", password="any"
        )

        with pytest.raises(EmailAlreadyRegisteredException):
            await use_case.execute(dto)

    async def test_register_duplicate_username(self, use_case, mock_user_repo):
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.get_by_username.return_value = MagicMock(spec=User)

        dto = RegisterUserDTO(
            email="new@test.com", username="occupied", password="any"
        )

        with pytest.raises(UsernameTakenException):
            await use_case.execute(dto)
