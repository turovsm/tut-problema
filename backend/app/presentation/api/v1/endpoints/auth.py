from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from app.application.dto.auth import (
    ChangePasswordDTO,
    ForgotPasswordDTO,
    LoginDTO,
    RefreshTokenDTO,
    RegisterUserDTO,
    ResendVerificationDTO,
    ResetPasswordDTO,
    VerifyEmailDTO,
)
from app.core.config import settings
from app.domain.entities.user import User
from app.presentation.api.deps import (
    get_change_password_use_case,
    get_current_user,
    get_forgot_password_use_case,
    get_login_use_case,
    get_logout_use_case,
    get_refresh_use_case,
    get_register_use_case,
    get_resend_verification_use_case,
    get_reset_password_use_case,
    get_verify_email_use_case,
)
from app.presentation.api.schemas.auth import (
    ChangePasswordRequest,
    EmailVerificationRequest,
    ForgotPasswordRequest,
    LoginRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    UserRegistration,
    UserResponse,
)
from app.presentation.api.schemas.common import SuccessResponse

router = APIRouter()


def set_auth_cookies(response: Response, result):
    is_secure = settings.APP_ENV == "production"

    response.set_cookie(
        key="access_token",
        value=f"Bearer {result.access_token}",
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=result.access_max_age,
    )
    response.set_cookie(
        key="refresh_token",
        value=result.refresh_token,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        max_age=result.refresh_max_age,
    )


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[UserResponse],
)
async def register(
    data: UserRegistration,
    use_case: Annotated[Depends, Depends(get_register_use_case)],
):
    user = await use_case.execute(
        RegisterUserDTO(
            email=data.email, username=data.username, password=data.password
        )
    )
    return SuccessResponse(
        data=UserResponse.model_validate(user),
        message="User registered successfully. Please check your email.",
    )


@router.post("/login", response_model=SuccessResponse[UserResponse])
async def login(
    data: LoginRequest,
    response: Response,
    use_case: Annotated[Depends, Depends(get_login_use_case)],
):
    result = await use_case.execute(
        LoginDTO(email=data.email, password=data.password)
    )
    set_auth_cookies(response, result)
    return SuccessResponse(
        data=UserResponse.model_validate(result.user),
        message="Successfully logged in",
    )


@router.post("/refresh", response_model=SuccessResponse[UserResponse])
async def refresh(
    request: Request,
    response: Response,
    use_case: Annotated[Depends, Depends(get_refresh_use_case)],
):
    token = request.cookies.get("refresh_token")
    result = await use_case.execute(RefreshTokenDTO(refresh_token=token or ""))
    set_auth_cookies(response, result)
    return SuccessResponse(
        data=UserResponse.model_validate(result.user), message="Token refreshed"
    )


@router.post("/logout", response_model=SuccessResponse[None])
async def logout(
    request: Request,
    response: Response,
    use_case: Annotated[Depends, Depends(get_logout_use_case)],
):
    token = request.cookies.get("refresh_token")
    await use_case.execute(RefreshTokenDTO(refresh_token=token or ""))
    response.delete_cookie("access_token", samesite="lax")
    response.delete_cookie("refresh_token", samesite="strict")
    return SuccessResponse(message="Successfully logged out")


@router.post("/verify-email", response_model=SuccessResponse[None])
async def verify_email(
    data: EmailVerificationRequest,
    use_case: Annotated[Depends, Depends(get_verify_email_use_case)],
):
    await use_case.execute(VerifyEmailDTO(token=data.token))
    return SuccessResponse(message="Email verified successfully")


@router.post("/resend-verification", response_model=SuccessResponse[None])
async def resend_verification(
    data: ResendVerificationRequest,
    use_case: Annotated[Depends, Depends(get_resend_verification_use_case)],
):
    await use_case.execute(ResendVerificationDTO(email=data.email))
    return SuccessResponse(message="If email exists and unverified, link sent.")


@router.post("/change-password", response_model=SuccessResponse[None])
async def change_password(
    data: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[Depends, Depends(get_change_password_use_case)],
):
    await use_case.execute(
        ChangePasswordDTO(
            user_id=current_user.id,
            current_password=data.current_password,
            new_password=data.new_password,
        )
    )
    return SuccessResponse(message="Password changed successfully")


@router.post("/forgot-password", response_model=SuccessResponse[None])
async def forgot_password(
    data: ForgotPasswordRequest,
    use_case: Annotated[Depends, Depends(get_forgot_password_use_case)],
):
    await use_case.execute(ForgotPasswordDTO(email=data.email))
    return SuccessResponse(message="If email exists, reset link sent.")


@router.post("/reset-password", response_model=SuccessResponse[None])
async def reset_password(
    data: ResetPasswordRequest,
    use_case: Annotated[Depends, Depends(get_reset_password_use_case)],
):
    await use_case.execute(
        ResetPasswordDTO(token=data.token, new_password=data.new_password)
    )
    return SuccessResponse(message="Password reset successfully")
