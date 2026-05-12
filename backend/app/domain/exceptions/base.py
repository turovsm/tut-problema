class DomainException(Exception):
    """Базовый класс для всех бизнес-исключений."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class EntityNotFoundException(DomainException):
    """Объект не найден."""

    pass


class AlreadyExistsException(DomainException):
    """Объект уже существует (например, email или голос)."""

    pass


class UnauthorizedException(DomainException):
    """Ошибка аутентификации."""

    pass


class PermissionDeniedException(DomainException):
    """Недостаточно прав для выполнения операции."""

    pass


class BusinessRuleException(DomainException):
    """Нарушение специфичного бизнес-правила (например, слишком большое расстояние)."""

    pass
