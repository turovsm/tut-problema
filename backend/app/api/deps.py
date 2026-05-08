from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.database.models.user import User
from app.database.session import get_db
from app.repositories.report_repository import ReportRepository
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.repositories.vote_repository import VoteRepository
from app.services.auth_service import AuthService
from app.services.report_service import ReportService
from app.services.vote_service import VoteService

security = HTTPBearer(auto_error=False)


# --- REPOSITORIES ---
def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_report_repo(db: AsyncSession = Depends(get_db)) -> ReportRepository:
    return ReportRepository(db)


def get_vote_repo(db: AsyncSession = Depends(get_db)) -> VoteRepository:
    return VoteRepository(db)


def get_token_repo(db: AsyncSession = Depends(get_db)) -> TokenRepository:
    return TokenRepository(db)


# --- SERVICES ---
def get_report_service(
    repo: ReportRepository = Depends(get_report_repo),
    vote_repo: VoteRepository = Depends(get_vote_repo),
) -> ReportService:
    return ReportService(repo, vote_repo)


def get_vote_service(
    vote_repo: VoteRepository = Depends(get_vote_repo),
    report_repo: ReportRepository = Depends(get_report_repo),
) -> VoteService:
    return VoteService(vote_repo, report_repo)


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repo),
    token_repo: TokenRepository = Depends(get_token_repo),
) -> AuthService:
    return AuthService(user_repo, token_repo)


# --- AUTHENTICATION ---
async def get_current_user(
    request: Request,
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    token = None
    cookie_auth = request.cookies.get("access_token")
    if cookie_auth:
        token = (
            cookie_auth.replace("Bearer ", "")
            if cookie_auth.startswith("Bearer ")
            else cookie_auth
        )
    if not token and credentials:
        token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    payload = decode_token(token, expected_type="access")
    if not payload or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    user = await user_repo.get(UUID(payload.get("sub")))
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
) -> Optional[User]:
    token = None
    cookie_auth = request.cookies.get("access_token")
    if cookie_auth:
        token = (
            cookie_auth.replace("Bearer ", "")
            if cookie_auth.startswith("Bearer ")
            else cookie_auth
        )
    if not token and credentials:
        token = credentials.credentials
    if not token:
        return None

    payload = decode_token(token, expected_type="access")
    if not payload or not payload.get("sub"):
        return None

    user = await user_repo.get(UUID(payload.get("sub")))
    if not user or not user.is_active:
        return None

    request.state.user_id = str(user.id)
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


def get_current_verified_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified."
        )
    return current_user


def get_current_moderator(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role not in ["moderator", "gov_org"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user
