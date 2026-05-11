from .base import BusinessRuleException, EntityNotFoundException


class ReportNotFoundException(EntityNotFoundException):
    def __init__(self):
        super().__init__("Report not found")


class DistanceTooFarException(BusinessRuleException):
    def __init__(self, distance: float, max_allowed: int):
        super().__init__(
            f"Distance {distance:.0f}m exceeds max allowed ({max_allowed}m)."
        )


class PhotoLimitExceededException(BusinessRuleException):
    def __init__(self, max_photos: int):
        super().__init__(f"Maximum {max_photos} photos per report.")


class MinPhotosRequiredException(BusinessRuleException):
    def __init__(self, min_photos: int):
        super().__init__(f"At least {min_photos} photo(s) required.")
