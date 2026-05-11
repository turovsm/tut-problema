from datetime import datetime, timezone


def get_utc_now_naive() -> datetime:
    """Возвращает текущее время UTC без информации о часовом поясе."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
