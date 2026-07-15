import logging
import sys
from typing import Any, MutableMapping

import structlog
from asgi_correlation_id import correlation_id

from app.core.config import settings

def setup_logging() -> None:
    
    #shared structlog processors
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    #Extract request correlation ID if available
    def add_correlation_id(
        logger: logging.Logger, 
        method_name: str, 
        event_dict: MutableMapping[str, Any]
    ) -> MutableMapping[str, Any]:
        req_id = correlation_id.get()
        if req_id:
            event_dict["request_id"] = req_id
        return event_dict

    shared_processors.insert(1, add_correlation_id)

    #formatter based on environment
    if settings.ENVIRONMENT.lower() == "production":
        formatter = structlog.processors.JSONRenderer()
    else:
        formatter = structlog.dev.ConsoleRenderer(colors=True)

    #structlog itself
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    #intercept standard library logging and route to structlog
    formatter_handler = logging.StreamHandler(sys.stdout)
    formatter_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                formatter,
            ],
        )
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(formatter_handler)
    root_logger.setLevel(logging.INFO)

    #override uvicorn loggers specifically so they format as JSON/Console
    for _log in ["uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"]:
        logger = logging.getLogger(_log)
        logger.handlers.clear()
        logger.propagate = True
