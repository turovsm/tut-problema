from .base import (
    AlreadyExistsException,
    BusinessRuleException,
    EntityNotFoundException,
    UnauthorizedException,
)


class UserNotFoundException(EntityNotFoundException):
    def __init__(self):
        super().__init__("User not found")


class EmailAlreadyRegisteredException(AlreadyExistsException):
    def __init__(self):
        super().__init__("Email already registered")


class UsernameTakenException(AlreadyExistsException):
    def __init__(self):
        super().__init__("Username already taken")


class UserInactiveException(UnauthorizedException):
    def __init__(self):
        super().__init__("Account is deactivated")


class EmailNotVerifiedException(BusinessRuleException):
    def __init__(self):
        super().__init__("Email not verified.")


class WeakPasswordException(BusinessRuleException):
    def __init__(self, details: str):
        super().__init__(f"Password does not meet requirements: {details}")
