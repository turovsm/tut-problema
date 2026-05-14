from .base import (
    AlreadyExistsException,
    BusinessRuleException,
    PermissionDeniedException,
)


class VoteAlreadyExistsException(AlreadyExistsException):
    def __init__(self):
        super().__init__("Vote already exists")


class SelfVotingException(PermissionDeniedException):
    def __init__(self):
        super().__init__("You cannot vote on your own report")


class VoteDistanceException(BusinessRuleException):
    def __init__(self, max_meters: int):
        super().__init__(
            f"Cannot vote. You must be within {max_meters} meters."
        )
