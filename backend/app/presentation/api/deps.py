from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.auth.change_password import (
    ChangePasswordUseCase,
)
from app.application.use_cases.auth.forgot_password import (
    ForgotPasswordUseCase,
)
from app.application.use_cases.auth.login_user import LoginUserUseCase
from app.application.use_cases.auth.logout_user import LogoutUserUseCase
from app.application.use_cases.auth.refresh_token import RefreshTokenUseCase

# --- Application Use Cases ---
from app.application.use_cases.auth.register_user import RegisterUserUseCase
from app.application.use_cases.auth.resend_verification import (
    ResendVerificationUseCase,
)
from app.application.use_cases.auth.reset_password import ResetPasswordUseCase
from app.application.use_cases.auth.verify_email import VerifyEmailUseCase
from app.application.use_cases.reports.add_report_photo import (
    AddReportPhotoUseCase,
)
from app.application.use_cases.reports.create_report import CreateReportUseCase
from app.application.use_cases.reports.delete_report import DeleteReportUseCase
from app.application.use_cases.reports.delete_report_photo import (
    DeleteReportPhotoUseCase,
)
from app.application.use_cases.reports.get_my_reports import (
    GetMyReportsUseCase,
)
from app.application.use_cases.reports.get_nearby_reports import (
    GetNearbyReportsUseCase,
)
from app.application.use_cases.reports.get_photo import GetPhotoUseCase
from app.application.use_cases.reports.get_report_by_id import (
    GetReportByIdUseCase,
)
from app.application.use_cases.reports.get_reports import GetReportsUseCase
from app.application.use_cases.reports.update_report import UpdateReportUseCase
from app.application.use_cases.users.get_user_profile import (
    GetUserProfileUseCase,
)
from app.application.use_cases.users.get_user_votes import GetUserVotesUseCase
from app.application.use_cases.users.list_all_users import ListAllUsersUseCase
from app.application.use_cases.users.update_user import UpdateUserUseCase
from app.application.use_cases.votes.cast_vote import CastVoteUseCase
from app.application.use_cases.votes.get_my_vote import GetMyVoteUseCase
from app.application.use_cases.votes.get_vote_stats import GetVoteStatsUseCase
from app.application.use_cases.votes.remove_vote import RemoveVoteUseCase
from app.core.config import settings
from app.domain.entities.enums import UserRole
from app.domain.entities.user import User
from app.infrastructure.database.repositories.report_repository import (
    ReportRepository,
)
from app.infrastructure.database.repositories.token_repository import (
    TokenRepository,
)

# --- Infrastructure Implementations ---
from app.infrastructure.database.repositories.user_repository import (
    UserRepository,
)
from app.infrastructure.database.repositories.vote_repository import (
    VoteRepository,
)
from app.infrastructure.database.session import get_db
from app.infrastructure.mail.console_email_provider import ConsoleEmailProvider
from app.infrastructure.security.auth_provider import JoseAuthProvider
from app.infrastructure.storage.local_storage_provider import (
    LocalStorageProvider,
)

# --- Infrastructure Providers ---
auth_provider = JoseAuthProvider()
email_provider = ConsoleEmailProvider()
storage_provider = LocalStorageProvider()

security = HTTPBearer(auto_error=False)


# --- REPOSITORY DEPENDENCIES ---
async def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


async def get_report_repo(
    db: AsyncSession = Depends(get_db),
) -> ReportRepository:
    return ReportRepository(db)


async def get_vote_repo(db: AsyncSession = Depends(get_db)) -> VoteRepository:
    return VoteRepository(db)


async def get_token_repo(db: AsyncSession = Depends(get_db)) -> TokenRepository:
    return TokenRepository(db)


# --- AUTH USE CASES ---
def get_register_use_case(
    u_repo: UserRepository = Depends(get_user_repo),
    t_repo: TokenRepository = Depends(get_token_repo),
) -> RegisterUserUseCase:
    return RegisterUserUseCase(
        u_repo,
        t_repo,
        auth_provider,
        email_provider,
        settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS,
    )


def get_login_use_case(
    u_repo: UserRepository = Depends(get_user_repo),
    t_repo: TokenRepository = Depends(get_token_repo),
) -> LoginUserUseCase:
    return LoginUserUseCase(
        u_repo,
        t_repo,
        auth_provider,
        settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )


def get_refresh_use_case(
    u_repo: UserRepository = Depends(get_user_repo),
    t_repo: TokenRepository = Depends(get_token_repo),
) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(
        u_repo,
        t_repo,
        auth_provider,
        settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )


def get_logout_use_case(
    t_repo: TokenRepository = Depends(get_token_repo),
) -> LogoutUserUseCase:
    return LogoutUserUseCase(t_repo, auth_provider)


def get_verify_email_use_case(
    u_repo: UserRepository = Depends(get_user_repo),
    t_repo: TokenRepository = Depends(get_token_repo),
) -> VerifyEmailUseCase:
    return VerifyEmailUseCase(u_repo, t_repo)


def get_resend_verification_use_case(
    u_repo: UserRepository = Depends(get_user_repo),
    t_repo: TokenRepository = Depends(get_token_repo),
) -> ResendVerificationUseCase:
    return ResendVerificationUseCase(
        u_repo,
        t_repo,
        email_provider,
        settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS,
    )


def get_change_password_use_case(
    u_repo: UserRepository = Depends(get_user_repo),
) -> ChangePasswordUseCase:
    return ChangePasswordUseCase(u_repo, auth_provider)


def get_forgot_password_use_case(
    u_repo: UserRepository = Depends(get_user_repo),
    t_repo: TokenRepository = Depends(get_token_repo),
) -> ForgotPasswordUseCase:
    return ForgotPasswordUseCase(
        u_repo,
        t_repo,
        email_provider,
        settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS,
    )


def get_reset_password_use_case(
    u_repo: UserRepository = Depends(get_user_repo),
    t_repo: TokenRepository = Depends(get_token_repo),
) -> ResetPasswordUseCase:
    return ResetPasswordUseCase(u_repo, t_repo, auth_provider)


# --- REPORT USE CASES ---
def get_create_report_use_case(
    r_repo: ReportRepository = Depends(get_report_repo),
) -> CreateReportUseCase:
    return CreateReportUseCase(
        r_repo,
        storage_provider,
        settings.MAX_REPORT_DISTANCE_METERS,
        settings.EARTH_RADIUS_METERS,
    )


def get_get_reports_use_case(
    r_repo: ReportRepository = Depends(get_report_repo),
    v_repo: VoteRepository = Depends(get_vote_repo),
) -> GetReportsUseCase:
    return GetReportsUseCase(r_repo, v_repo)


def get_report_by_id_use_case(
    r_repo: ReportRepository = Depends(get_report_repo),
    v_repo: VoteRepository = Depends(get_vote_repo),
) -> GetReportByIdUseCase:
    return GetReportByIdUseCase(r_repo, v_repo)


def get_nearby_reports_use_case(
    r_repo: ReportRepository = Depends(get_report_repo),
    v_repo: VoteRepository = Depends(get_vote_repo),
) -> GetNearbyReportsUseCase:
    return GetNearbyReportsUseCase(r_repo, v_repo)


def get_my_reports_use_case(
    r_repo: ReportRepository = Depends(get_report_repo),
) -> GetMyReportsUseCase:
    return GetMyReportsUseCase(r_repo)


def get_update_report_use_case(
    r_repo: ReportRepository = Depends(get_report_repo),
) -> UpdateReportUseCase:
    return UpdateReportUseCase(r_repo)


def get_delete_report_use_case(
    r_repo: ReportRepository = Depends(get_report_repo),
) -> DeleteReportUseCase:
    return DeleteReportUseCase(r_repo, storage_provider)


def get_add_photo_use_case(
    r_repo: ReportRepository = Depends(get_report_repo),
) -> AddReportPhotoUseCase:
    return AddReportPhotoUseCase(
        r_repo, storage_provider, settings.MAX_PHOTOS_PER_REPORT
    )


def get_delete_photo_use_case(
    r_repo: ReportRepository = Depends(get_report_repo),
) -> DeleteReportPhotoUseCase:
    return DeleteReportPhotoUseCase(
        r_repo, storage_provider, settings.MIN_PHOTOS_PER_REPORT
    )


def get_photo_use_case(
    r_repo: ReportRepository = Depends(get_report_repo),
) -> GetPhotoUseCase:
    return GetPhotoUseCase(r_repo)


# --- VOTE USE CASES ---
def get_cast_vote_use_case(
    v_repo: VoteRepository = Depends(get_vote_repo),
    r_repo: ReportRepository = Depends(get_report_repo),
) -> CastVoteUseCase:
    return CastVoteUseCase(
        v_repo,
        r_repo,
        settings.MAX_VOTE_DISTANCE_METERS,
        settings.VOTE_VERIFICATION_BUFFER_METERS,
        settings.EARTH_RADIUS_METERS,
    )


def get_remove_vote_use_case(
    v_repo: VoteRepository = Depends(get_vote_repo),
) -> RemoveVoteUseCase:
    return RemoveVoteUseCase(v_repo)


def get_vote_stats_use_case(
    v_repo: VoteRepository = Depends(get_vote_repo),
    r_repo: ReportRepository = Depends(get_report_repo),
) -> GetVoteStatsUseCase:
    return GetVoteStatsUseCase(v_repo, r_repo)


def get_my_vote_use_case(
    v_repo: VoteRepository = Depends(get_vote_repo),
) -> GetMyVoteUseCase:
    return GetMyVoteUseCase(v_repo)


# --- USER USE CASES ---
def get_user_profile_use_case(
    u_repo: UserRepository = Depends(get_user_repo),
) -> GetUserProfileUseCase:
    return GetUserProfileUseCase(u_repo)


def get_update_user_use_case(
    u_repo: UserRepository = Depends(get_user_repo),
) -> UpdateUserUseCase:
    return UpdateUserUseCase(u_repo)


def get_user_votes_use_case(
    v_repo: VoteRepository = Depends(get_vote_repo),
) -> GetUserVotesUseCase:
    return GetUserVotesUseCase(v_repo)


def get_list_all_users_use_case(
    u_repo: UserRepository = Depends(get_user_repo),
) -> ListAllUsersUseCase:
    return ListAllUsersUseCase(u_repo)


# --- AUTHENTICATION DEPENDENCY ---
async def get_current_user(
    request: Request,
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    token = None
    # 1. Проверяем Cookie
    cookie_auth = request.cookies.get("access_token")
    if cookie_auth:
        token = (
            cookie_auth.replace("Bearer ", "")
            if cookie_auth.startswith("Bearer ")
            else cookie_auth
        )

    # 2. Проверяем Header, если в Cookie пусто
    if not token and credentials:
        token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    payload = auth_provider.decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    user_id = payload.get("sub")
    user = await user_repo.get_by_id(UUID(user_id))

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User inactive or deleted",
        )

    request.state.user_id = str(user.id)
    return user


async def get_optional_current_user(
    request: Request,
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User | None:
    try:
        return await get_current_user(request, user_repo, credentials)
    except HTTPException:
        return None


def get_current_verified_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified."
        )
    return current_user


def get_current_moderator(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in [UserRole.MODERATOR, UserRole.GOV_ORG]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user
