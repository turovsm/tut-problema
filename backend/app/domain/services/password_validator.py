from app.domain.exceptions.user import WeakPasswordException


class PasswordValidator:
    @staticmethod
    def validate(
        password: str,
        min_length: int = 8,
        max_length: int = 128,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digits: bool = True,
        require_special: bool = True,
        special_chars: str = "@$!%*?&",
        forbidden_passwords: list[str] | None = None,
    ) -> None:
        if len(password) < min_length:
            raise WeakPasswordException(
                f"at least {min_length} characters long"
            )

        if len(password) > max_length:
            raise WeakPasswordException(f"at most {max_length} characters long")

        if require_uppercase and not any(c.isupper() for c in password):
            raise WeakPasswordException("at least one uppercase letter")

        if require_lowercase and not any(c.islower() for c in password):
            raise WeakPasswordException("at least one lowercase letter")

        if require_digits and not any(c.isdigit() for c in password):
            raise WeakPasswordException("at least one digit")

        if require_special and not any(c in special_chars for c in password):
            raise WeakPasswordException(
                f"at least one special character from: {special_chars}"
            )

        if forbidden_passwords and password.lower() in [
            p.lower() for p in forbidden_passwords
        ]:
            raise WeakPasswordException("too common and easily guessable")
