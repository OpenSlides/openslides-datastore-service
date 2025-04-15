from contextlib import nullcontext
from typing import Any, Dict

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from datastore.shared.di import injector
from datastore.shared.services import EnvironmentService


OTEL_DATA_FIELD_KEY = TraceContextTextMapPropagator._TRACEPARENT_HEADER_NAME
otel_initialized = False


def is_otel_enabled():
    """
    Determine if OpenTelemetry is enable per environment variable.
    """
    env_service = injector.get(EnvironmentService)
    return env_service.is_otel_enabled()


def get_span_exporter():
    return OTLPSpanExporter(endpoint="http://collector:4317", insecure=True)


def init(service_name):
    """
    Initializes the opentelemetry components and connection to the otel collector.
    """
    if not is_otel_enabled():
        return
    tracer_provider = TracerProvider(
        resource=Resource.create({SERVICE_NAME: service_name})
    )
    trace.set_tracer_provider(tracer_provider)
    span_processor = BatchSpanProcessor(get_span_exporter())
    tracer_provider.add_span_processor(span_processor)
    global otel_initialized
    otel_initialized = True


def instrument_flask(app):
    FlaskInstrumentor().instrument_app(app)


def instrument_redis():
    RedisInstrumentor().instrument()


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

    assert (
        otel_initialized
    ), "datastore:Opentelemetry span to be set before having set a TRACER_PROVIDER"

    tracer = trace.get_tracer_provider().get_tracer(__name__)
    span = tracer.start_as_current_span(name, attributes=attributes)

    return span


def inject_otel_data(fields: Dict[str, Any]) -> None:
    if is_otel_enabled():
        TraceContextTextMapPropagator().inject(fields)
