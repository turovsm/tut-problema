import pytest

from app.core.utils.distance import calculate_distance_haversine


class TestDistanceUtils:
    def test_zero_distance(self):
        lat, lon = 55.7558, 37.6176
        distance = calculate_distance_haversine(lat, lon, lat, lon)
        assert distance == 0.0

    def test_small_distance_accuracy(self):
        lat1, lon1 = 55.7558, 37.6176
        lat2, lon2 = 55.7559, 37.6177
        distance = calculate_distance_haversine(lat1, lon1, lat2, lon2)
        assert 12.0 < distance < 13.0

    def test_large_distance_known_points(self):
        dist_meters = calculate_distance_haversine(
            55.7558, 37.6176, 59.9343, 30.3351
        )
        dist_km = dist_meters / 1000
        assert 630.0 < dist_km < 640.0

    def test_custom_earth_radius(self):
        lat1, lon1, lat2, lon2 = 0.0, 0.0, 1.0, 0.0
        dist_normal = calculate_distance_haversine(
            lat1, lon1, lat2, lon2, earth_radius=6371000
        )
        dist_small = calculate_distance_haversine(
            lat1, lon1, lat2, lon2, earth_radius=3185500
        )
        assert pytest.approx(dist_normal / 2, rel=1e-5) == dist_small

    def test_antipodes(self):
        distance = calculate_distance_haversine(0, 0, 0, 180)
        expected = 3.1415926535 * 6371000
        assert pytest.approx(distance, rel=1e-3) == expected
