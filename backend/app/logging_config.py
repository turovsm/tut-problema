import logging
import sys
from typing import Any

import structlog
from structlog.contextvars import merge_contextvars
from structlog.types import EventDict, Processor

from app.config import settings


def add_app_context(_: Any, __: Any, event_dict: EventDict) -> EventDict:
    if settings.LOG_INCLUDE_APP_NAME:
        event_dict["app_name"] = settings.APP_NAME
        event_dict["app_env"] = settings.APP_ENV
    return event_dict


def drop_color_message_key(_: Any, __: Any, event_dict: EventDict) -> EventDict:
    event_dict.pop("color_message", None)
    return event_dict


def filter_health_check_logs(_, __, event_dict: EventDict) -> EventDict:
    path = event_dict.get("path", "")
    if path in ["/health", "/health/detailed"] and event_dict.get("event") in ["Request started", "Request completed"]:
        event_dict["_skip"] = True
    return event_dict


def setup_logging() -> None:
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    shared_processors: list[Processor] = [
        merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        filter_health_check_logs,
    ]

    if settings.LOG_INCLUDE_TIMESTAMP:
        shared_processors.append(structlog.processors.TimeStamper(fmt="iso"))

    shared_processors.extend([
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        drop_color_message_key,
        add_app_context,
    ])

    if settings.LOG_FORMAT.lower() == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [renderer],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("uvicorn.access").setLevel(log_level)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logger = structlog.get_logger()
    logger.info("Logging initialized", log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)


def get_logger(name: str = None):
    logger = structlog.get_logger(name)
    return logger
