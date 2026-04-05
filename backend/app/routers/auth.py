import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import User as UserModel, RefreshToken, VerificationToken
from app.database import get_db
from app.dependencies import get_current_active_user
from app.email import email_service
from app.logging_config import get_logger
from app.rate_limiter import rate_limit_auth
from app.schemas import (
    UserRegistration, LoginRequest, TokenResponse, User as UserSchema,
    RefreshTokenRequest, ChangePasswordRequest, ForgotPasswordRequest,
    ResetPasswordRequest, EmailVerificationRequest, ResendVerificationRequest,
    SuccessResponse
)
from app.security import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, decode_token, generate_jti
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = get_logger("app.routers.auth")

DBSession = Annotated[AsyncSession, Depends(get_db)]
Background = Annotated[BackgroundTasks, None]
CurrentUser = Annotated[UserModel, Depends(get_current_active_user)]


def create_user_schema(user: UserModel) -> UserSchema:
    return UserSchema.model_validate(user)


def create_verification_token(user_id: UUID) -> VerificationToken:
    return VerificationToken(
        user_id=user_id,
        token=uuid.uuid4(),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)
    )


def create_refresh_token_record(user_id: UUID, jti: str) -> RefreshToken:
    return RefreshToken(
        jti=jti,
        user_id=user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )


def create_token_response(user: UserModel, access_token: str, refresh_token_value: str) -> TokenResponse:
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_value,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_expires_in=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        user=create_user_schema(user)
    )


async def generate_and_store_tokens(user: UserModel, db: AsyncSession) -> tuple[str, str]:
    access_token = create_access_token(str(user.id))
    jti = generate_jti()
    refresh_token_value = create_refresh_token(str(user.id), jti)

    db_refresh_token = create_refresh_token_record(user.id, jti)
    db.add(db_refresh_token)
    await db.commit()

    return access_token, refresh_token_value


@router.post("/register", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
async def register(
        user_data: UserRegistration,
        db: DBSession,
        background_tasks: Background
):
    logger.info("Registration attempt", email=user_data.email, username=user_data.username)

    result = await db.execute(select(UserModel).where(UserModel.email == user_data.email))
    existing_email = result.scalar_one_or_none()
    if existing_email:
        logger.warning("Registration failed - email already exists", email=user_data.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    result = await db.execute(select(UserModel).where(UserModel.username == user_data.username))
    existing_username = result.scalar_one_or_none()
    if existing_username:
        logger.warning("Registration failed - username already exists", username=user_data.username)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    user = UserModel(
        email=str(user_data.email),
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        is_active=True,
        is_verified=False
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    verification_token = create_verification_token(user.id)
    db.add(verification_token)
    await db.commit()

    background_tasks.add_task(
        email_service.send_verification_email,
        user.email,
        user.username,
        str(verification_token.token)
    )

    logger.info("User registered successfully", user_id=str(user.id), email=user.email)

    return SuccessResponse(
        data=create_user_schema(user).model_dump(),
        message="User registered successfully. Please check your email for verification."
    )


@router.post("/login", response_model=TokenResponse)
async def login(
        login_data: LoginRequest,
        db: DBSession
):
    logger.info("Login attempt", email=login_data.email)

    result = await db.execute(select(UserModel).where(UserModel.email == login_data.email))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning("Login failed - user not found", email=login_data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(login_data.password, user.password_hash):
        logger.warning("Login failed - invalid password", user_id=str(user.id), email=login_data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning("Login failed - account deactivated", user_id=str(user.id))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    access_token, refresh_token_value = await generate_and_store_tokens(user, db)

    logger.info("User logged in successfully", user_id=str(user.id))

    return create_token_response(user, access_token, refresh_token_value)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
        refresh_data: RefreshTokenRequest,
        db: DBSession
):
    logger.info("Token refresh attempt")

    payload = decode_token(refresh_data.refresh_token, expected_type="refresh")
    if not payload:
        logger.warning("Token refresh failed - invalid token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    jti = payload.get("jti")
    user_id_str = payload.get("sub")

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.jti == jti,
            RefreshToken.revoked_at.is_(None)
        )
    )
    stored_token = result.scalar_one_or_none()

    if not stored_token or stored_token.expires_at < datetime.now(timezone.utc):
        logger.warning("Token refresh failed - token expired or revoked", jti=jti)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired or revoked"
        )

    result = await db.execute(select(UserModel).where(UserModel.id == UUID(user_id_str)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        logger.warning("Token refresh failed - user not found or inactive", user_id=user_id_str)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    stored_token.revoked_at = datetime.now(timezone.utc)
    await db.commit()

    access_token, refresh_token_value = await generate_and_store_tokens(user, db)

    logger.info("Token refreshed successfully", user_id=str(user.id))

    return create_token_response(user, access_token, refresh_token_value)


@router.post("/logout")
async def logout(
        refresh_data: RefreshTokenRequest,
        db: DBSession
):
    logger.info("Logout attempt")

    payload = decode_token(refresh_data.refresh_token, expected_type="refresh")
    if payload:
        jti = payload.get("jti")
        result = await db.execute(select(RefreshToken).where(RefreshToken.jti == jti))
        token = result.scalar_one_or_none()
        if token:
            token.revoked_at = datetime.now(timezone.utc)
            await db.commit()
            logger.info("Token revoked on logout", jti=jti)

    return SuccessResponse(message="Successfully logged out")


@router.post("/verify-email")
async def verify_email(
        verification_data: EmailVerificationRequest,
        db: DBSession
):
    logger.info("Email verification attempt", token=str(verification_data.token))

    result = await db.execute(
        select(VerificationToken).where(VerificationToken.token == verification_data.token)
    )
    token = result.scalar_one_or_none()

    if not token:
        logger.warning("Email verification failed - invalid token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )

    now = datetime.now(timezone.utc)
    token_expires = token.expires_at
    if token_expires.tzinfo is None:
        token_expires = token_expires.replace(tzinfo=timezone.utc)

    if token_expires < now:
        logger.warning("Email verification failed - token expired", user_id=str(token.user_id))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired"
        )

    result = await db.execute(select(UserModel).where(UserModel.id == token.user_id))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning("Email verification failed - user not found", user_id=str(token.user_id))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_verified = True
    await db.delete(token)
    await db.commit()

    logger.info("Email verified successfully", user_id=str(user.id))

    return SuccessResponse(message="Email verified successfully")


@router.post("/resend-verification")
async def resend_verification(
        resend_data: ResendVerificationRequest,
        db: DBSession,
        background_tasks: Background
):
    logger.info("Resend verification email requested", email=resend_data.email)

    result = await db.execute(select(UserModel).where(UserModel.email == resend_data.email))
    user = result.scalar_one_or_none()

    if not user:
        logger.info("Resend verification - user not found (security - returning success)", email=resend_data.email)
        return SuccessResponse(message="If your email is registered, you will receive a verification link")

    if user.is_verified:
        logger.info("Resend verification - email already verified", user_id=str(user.id))
        return SuccessResponse(message="Email already verified")

    await db.execute(delete(VerificationToken).where(VerificationToken.user_id == user.id))

    new_token = create_verification_token(user.id)
    db.add(new_token)
    await db.commit()

    background_tasks.add_task(
        email_service.send_verification_email,
        user.email,
        user.username,
        str(new_token.token)
    )

    logger.info("Verification email resent", user_id=str(user.id))

    return SuccessResponse(message="Verification email sent")


@router.post("/change-password")
async def change_password(
        password_data: ChangePasswordRequest,
        db: DBSession,
        current_user: CurrentUser
):
    logger.info("Password change attempt", user_id=str(current_user.id))

    if not verify_password(password_data.current_password, current_user.password_hash):
        logger.warning("Password change failed - incorrect current password", user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )

    current_user.password_hash = hash_password(password_data.new_password)
    await db.commit()

    logger.info("Password changed successfully", user_id=str(current_user.id))

    return SuccessResponse(message="Password changed successfully")


@router.post("/forgot-password", dependencies=[Depends(rate_limit_auth)])
async def forgot_password(
        forgot_data: ForgotPasswordRequest,
        db: DBSession,
        background_tasks: Background
):
    logger.info("Password reset requested", email=forgot_data.email)

    result = await db.execute(select(UserModel).where(UserModel.email == forgot_data.email))
    user = result.scalar_one_or_none()

    if user:
        reset_token = create_verification_token(user.id)
        reset_token.expires_at = datetime.now(timezone.utc) + timedelta(
            hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
        db.add(reset_token)
        await db.commit()

        background_tasks.add_task(
            email_service.send_password_reset_email,
            user.email,
            user.username,
            str(reset_token.token)
        )
        logger.info("Password reset email sent", user_id=str(user.id))

    return SuccessResponse(message="If your email is registered, you will receive a password reset link")


@router.post("/reset-password", dependencies=[Depends(rate_limit_auth)])
async def reset_password(
        reset_data: ResetPasswordRequest,
        db: DBSession
):
    logger.info("Password reset attempt")

    result = await db.execute(
        select(VerificationToken).where(VerificationToken.token == reset_data.token)
    )
    token = result.scalar_one_or_none()

    if not token:
        logger.warning("Password reset failed - invalid token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    token_expires = token.expires_at
    if token_expires.tzinfo is None:
        token_expires = token_expires.replace(tzinfo=timezone.utc)

    if token_expires < datetime.now(timezone.utc):
        logger.warning("Password reset failed - token expired", user_id=str(token.user_id))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    result = await db.execute(select(UserModel).where(UserModel.id == token.user_id))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning("Password reset failed - user not found", user_id=str(token.user_id))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.password_hash = hash_password(reset_data.new_password)
    await db.delete(token)
    await db.commit()

    logger.info("Password reset successfully", user_id=str(user.id))

    return SuccessResponse(message="Password reset successfully")
