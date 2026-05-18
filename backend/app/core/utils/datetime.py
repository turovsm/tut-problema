from datetime import UTC, datetime


def get_utc_now_naive() -> datetime:
    """Возвращает текущее время UTC без информации о часовом поясе."""
    return datetime.now(UTC).replace(tzinfo=None)
