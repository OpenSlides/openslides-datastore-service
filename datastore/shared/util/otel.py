from abc import ABC
from contextlib import nullcontext
from typing import Any, Dict

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from datastore.shared.di import injector
from datastore.shared.services import EnvironmentService


OTEL_DATA_FIELD_KEY = "__otel_data"


def is_otel_enabled():
    """
    Determine if OpenTelemetry is enable per environment variable.
    """
    env_service = injector.get(EnvironmentService)
    return env_service.is_otel_enabled()


def init(service_name):
    """
    Initializes the opentelemetry components and connection to the otel collector.
    """
    if not is_otel_enabled():
        return

    if not trace.get_tracer_provider():
        span_exporter = OTLPSpanExporter(
            endpoint="http://collector:4317",
            insecure=True
            # optional
            # credentials=ChannelCredentials(credentials),
            # headers=(("metadata", "metadata")),
        )
        tracer_provider = TracerProvider(
            resource=Resource.create({SERVICE_NAME: service_name})
        )
        trace.set_tracer_provider(tracer_provider)
        span_processor = BatchSpanProcessor(span_exporter)
        tracer_provider.add_span_processor(span_processor)


def instrument_flask(app):
    FlaskInstrumentor().instrument_app(app)


def make_span(name, attributes=None):
    """
    Returns a new child span to the currently active span.
    If OPENTELEMETRY_ENABLED is not truthy a nullcontext will be returned instead.
    So at any point in the code this function can be called in a with statement
    without any additional checking needed.

    Example:
    ```
    with make_span("foo") as span:
        ...
        with make_span("bar", { "key": "value", ... }) as subspan:
            ...
    ```
    """
    if not is_otel_enabled():
        return nullcontext()

    print(f"datastore/otel.py make_service span_name:{name}")
    assert (tracer_provider := trace.get_tracer_provider()), "Opentelemetry span to be set before having set a TRACER_PROVIDER"
    tracer = tracer_provider.get_tracer(__name__)
    span = tracer.start_as_current_span(name, attributes=attributes)

    return span


def inject_otel_data(fields: Dict[str, Any]) -> None:
    if not is_otel_enabled():
        return

    span_context = trace.get_current_span().get_span_context()
    trace_id = span_context.trace_id
    span_id = span_context.span_id
    span_data = f"{trace_id}:{span_id}:{span_context.trace_flags}"
    fields[OTEL_DATA_FIELD_KEY] = span_data
