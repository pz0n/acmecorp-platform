import json
import logging
import sys
from datetime import datetime, timezone

from opentelemetry import trace


class JsonFormatter(logging.Formatter):
    def format(
        self,
        record: logging.LogRecord,
    ) -> str:
        log_record = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "service": "payments-api",
            "message": record.getMessage(),
        }

        span = trace.get_current_span()
        span_context = span.get_span_context()

        if span_context.is_valid:
            log_record["trace_id"] = format(
                span_context.trace_id,
                "032x",
            )
            log_record["span_id"] = format(
                span_context.span_id,
                "016x",
            )

        extra_fields = (
            "request_id",
            "method",
            "path",
            "status_code",
            "duration_ms",
            "order_id",
        )

        for field in extra_fields:
            value = getattr(
                record,
                field,
                None,
            )

            if value is not None:
                log_record[field] = value

        if record.exc_info:
            log_record["exception"] = (
                self.formatException(
                    record.exc_info
                )
            )

        return json.dumps(log_record)


def configure_logging() -> None:
    handler = logging.StreamHandler(
        sys.stdout
    )

    handler.setFormatter(
        JsonFormatter()
    )

    logger = logging.getLogger(
        "acmecorp"
    )

    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False