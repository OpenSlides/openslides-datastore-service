import os
from abc import ABC
from contextlib import nullcontext
from typing import Any, Dict

from datastore.shared.di import injector
from datastore.shared.services import EnvironmentService

from opentelemetry import propagators
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.propagate import get_global_textmap
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

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

    span_exporter = OTLPSpanExporter(
        endpoint=f"http://collector:4317",
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

    tracer = trace.get_tracer_provider().get_tracer(__name__)
    span = tracer.start_as_current_span(name, attributes=attributes)

    return span

class FqfieldsSetter(ABC):
    def set(self, carrier: Dict[str, Any], key: str, value: Any) -> None:
        if OTEL_DATA_FIELD_KEY not in carrier:
            carrier[OTEL_DATA_FIELD_KEY] = {}
        carrier[OTEL_DATA_FIELD_KEY][key] = value

def inject_otel_data(fields: Dict[str, Any]) -> None:
    if not is_otel_enabled():
        return

    def cb_set_opentelemetry_field(data: Dict[str, Any], key: str, value: str) -> None:
        if OTEL_DATA_FIELD_KEY not in data:
            data[OTEL_DATA_FIELD_KEY] = {}
        data[OTEL_DATA_FIELD_KEY][key] = value

    # print("ATTENTION")

    # print("span_context = trace.get_current_span().get_span_context()")
    span_context = trace.get_current_span().get_span_context()
    # print("propa = propagators.get_global_textmap()")
    propa = get_global_textmap()
    # print("propa.inject(cb_set_opentelemetry_field, fields, context=span_context)")
    propa.inject(
        carrier=fields,
        setter=FqfieldsSetter
    )
    
    print("print(fields)")
    print(fields)

    # trace_id_hex = span_context.trace_id.to_bytes(((span_context.trace_id.bit_length() + 7) // 8),"big").hex()
    # span_id_hex = span_context.span_id.to_bytes((( span_context.span_id.bit_length() + 7) // 8),"big").hex()
    # span_data = f"{trace_id_hex}:{span_id_hex}:{span_context.trace_flags}"
    return { OTEL_DATA_FIELD_KEY: span_data }




