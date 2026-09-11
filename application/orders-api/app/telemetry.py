import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    PeriodicExportingMetricReader,
)

def configure_tracing() -> None:
    service_name = os.getenv(
        "OTEL_SERVICE_NAME",
        "orders-api",
    )

    otlp_endpoint = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://otel-collector:4317",
    )

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": "0.5.0",
            "deployment.environment": "local",
        }
    )

    tracer_provider = TracerProvider(
        resource=resource,
    )

    exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=True,
    )

    tracer_provider.add_span_processor(
        BatchSpanProcessor(exporter)
    )

    trace.set_tracer_provider(tracer_provider)


def configure_metrics() -> None:
    service_name = os.getenv(
        "OTEL_SERVICE_NAME",
        "orders-api",
    )

    otlp_endpoint = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://otel-collector:4317",
    )

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": "0.6.0",
            "deployment.environment": "local",
        }
    )

    exporter = OTLPMetricExporter(
        endpoint=otlp_endpoint,
        insecure=True,
    )

    reader = PeriodicExportingMetricReader(
        exporter,
        export_interval_millis=10000,
    )

    provider = MeterProvider(
        resource=resource,
        metric_readers=[reader],
    )

    metrics.set_meter_provider(provider)