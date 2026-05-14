from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    longitude: float
    latitude: float
