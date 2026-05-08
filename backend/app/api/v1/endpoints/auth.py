from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)

from app.api.deps import get_auth_service, get_current_active_user
from app.core.config import settings
from app.database.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    EmailVerificationRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    UserDataWrapper,
    UserRegistration,
)
from app.schemas.common import SuccessResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[UserResponse],
)
async def register(
    user_data: UserRegistration,
    background_tasks: BackgroundTasks,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    try:
        user = await auth_service.register_user(
            user_data.model_dump(), background_tasks
        )
        return SuccessResponse(
            data=user,
            message="User registered successfully. Please check your email.",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.post("/login", response_model=SuccessResponse[UserDataWrapper])
async def login(
    login_data: LoginRequest,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    try:
        (
            user,
            access_token,
            refresh_token,
        ) = await auth_service.authenticate_user(
            login_data.email, login_data.password
        )
        secure_cookie = settings.APP_ENV == "production"
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            secure=secure_cookie,
            samesite="lax",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=secure_cookie,
            samesite="strict",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )
        return SuccessResponse(message="Login successful", data={"user": user})
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e)
        )


@router.post("/refresh", response_model=SuccessResponse[UserDataWrapper])
async def refresh_token(
    request: Request,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing from cookies",
        )
    try:
        (
            user,
            access_token,
            new_refresh_token,
        ) = await auth_service.refresh_tokens(refresh_token)
        secure_cookie = settings.APP_ENV == "production"
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            secure=secure_cookie,
            samesite="lax",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=secure_cookie,
            samesite="strict",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )
        return SuccessResponse(message="Tokens refreshed", data={"user": user})
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        )


@router.post("/logout", response_model=SuccessResponse[None])
async def logout(
    request: Request,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        await auth_service.logout(refresh_token)
    response.delete_cookie(key="access_token", samesite="lax")
    response.delete_cookie(key="refresh_token", samesite="strict")
    return SuccessResponse(message="Successfully logged out")


@router.post("/verify-email", response_model=SuccessResponse[None])
async def verify_email(
    data: EmailVerificationRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    try:
        await auth_service.verify_email(data.token)
        return SuccessResponse(message="Email verified successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.post("/resend-verification", response_model=SuccessResponse[None])
async def resend_verification(
    data: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    await auth_service.resend_verification(data.email, background_tasks)
    return SuccessResponse(
        message="If email is registered and unverified, link sent."
    )


@router.post("/change-password", response_model=SuccessResponse[None])
async def change_password(
    data: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    try:
        await auth_service.change_password(
            current_user.id, data.current_password, data.new_password
        )
        return SuccessResponse(message="Password changed successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        )


@router.post("/forgot-password", response_model=SuccessResponse[None])
async def forgot_password(
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    await auth_service.initiate_password_reset(data.email, background_tasks)
    return SuccessResponse(
        message="If email is registered, you will receive a reset link."
    )


@router.post("/reset-password", response_model=SuccessResponse[None])
async def reset_password(
    data: ResetPasswordRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    try:
        await auth_service.reset_password(data.token, data.new_password)
        return SuccessResponse(message="Password reset successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
