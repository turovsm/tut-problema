from math import atan2, cos, radians, sin, sqrt


def calculate_distance_haversine(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    earth_radius: float = 6371000.0,
) -> float:

    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius * c
