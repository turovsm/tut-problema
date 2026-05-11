from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    MODERATOR = "moderator"
    GOV_ORG = "gov_org"


class IssueType(str, Enum):
    SNOW = "snow"
    POTHOLE = "pothole"
    ROAD_OBSTRUCTION = "road_obstruction"
    FLOODING = "flooding"
    BROKEN_STREETLIGHT = "broken_streetlight"
    BROKEN_SIDEWALK = "broken_sidewalk"
    WATER_LEAK = "water_leak"
    SEWER_OVERFLOW = "sewer_overflow"
    ILLEGAL_DUMPING = "illegal_dumping"
    OTHER = "other"


class ReportStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DISMISSED = "dismissed"
    RESOLVED = "resolved"


class VoteType(str, Enum):
    CONFIRM = "confirm"
    DISMISS = "dismiss"
